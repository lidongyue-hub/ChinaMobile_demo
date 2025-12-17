import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.config import settings
from src.prompt import SYSTEM_PROMPT
from src.services.llm_client import _get_client
from src.db.session import get_db
from src.crud.crud_conversations import crud_conversations
from src.crud.crud_messages import crud_messages
from src.db.models import Conversation, Message
from src.schemas.ai import (
    ChatCompletionRequest,
    ConversationOut,
    ConversationSyncRequest,
    ExtractRequest,
    MessageOut,
)
from src.utils.parse_file_utils import parse_file_content

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _format_parsed_files(parsed: List[Dict[str, str]]) -> str:
    """仿前端 formatParsedFilesForPrompt 的格式化输出。"""
    if not parsed:
        return ""

    parts: List[str] = []
    for idx, pf in enumerate(parsed, start=1):
        header = f"=== 文件 {idx}: {pf.get('name', 'file')} ==="
        content = pf.get("content", "") or "[解析为空]"
        if len(content) > 15000:
            content = content[:15000] + "\n...[内容过长，已截断]"
        parts.append(f"{header}\n{content}")

    return (
        "以下是用户上传的文件内容，请基于这些内容进行分析：\n\n"
        f"{'\n\n'.join(parts)}\n\n---\n\n请根据以上文件内容回答用户的问题：\n\n"
    )


@router.post("/files/parse")
async def parse_files(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """解析上传文件并返回拼接后的上下文文本。"""
    parsed_files: List[Dict[str, str]] = []
    
    logger.info(f"Parsing {len(files)} files")

    for file in files:
        name = file.filename or "file"
        try:
            logger.info(f"Processing file: {name}")
            # 使用解析服务对文件进行解析，支持多种文件格式，并返回解析后的文本
            result = await parse_file_content(file)
            parsed_files.append({"name": result["name"], "content": result["content"]})
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to parse file {name}: {exc}", exc_info=True)
            parsed_files.append(
                {"name": name, "content": f"[解析失败: {exc}]"}
            )

    formatted = _format_parsed_files(parsed_files)
    return {"parsed_files": parsed_files, "formatted": formatted}


async def _stream_chat(params: Dict[str, Any]) -> AsyncGenerator[str, None]:
    client = _get_client()
    try:
        stream = await client.chat.completions.create(stream=True, **params)
    except Exception as exc:  # noqa: BLE001
        # 将错误作为 SSE 事件返回，避免已开始的响应再次抛异常
        err_payload = {"error": str(exc)}
        yield f"data: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
        return

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        delta_payload: Dict[str, Any] = {}
        content = getattr(delta, "content", None)
        if content:
            delta_payload["content"] = content
        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            delta_payload["reasoning_content"] = reasoning

        payload = {"choices": [{"delta": delta_payload, "finish_reason": None}]}
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # 结束标记
    yield "data: [DONE]\n\n"


@router.post("/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest, db: AsyncSession = Depends(get_db)
):
    """代理 LLM 聊天，支持流式返回，SSE 兼容前端解码。"""
    model_name = req.model or settings.LLM_DEFAULT_MODEL
    logger.info(f"Chat completion request: model={model_name}, conversation_id={req.conversation_id}")
    
    if not model_name:
        raise HTTPException(status_code=400, detail="model 未配置")

    params: Dict[str, Any] = {
        "model": model_name,
    }
    # 构造历史 + 当前消息：后端从 DB 取
    history: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if req.conversation_id:
        history_msgs = await crud_messages.list_messages(
            db=db, conversation_id=req.conversation_id, limit=200
        )
        for m in history_msgs:
            history.append({"role": m.role, "content": m.content})

    # 追加本次传入的消息（通常只有当前 user 消息）
    history.append({"role": "user", "content": req.message})
    params["messages"] = history
    params["max_tokens"] = settings.LLM_MAX_TOKENS
    params["temperature"] = settings.LLM_TEMPERATURE
    stream_flag = settings.LLM_STREAM

    if stream_flag:
        generator = _stream_chat(params)
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    client = _get_client()
    try:
        resp = await client.chat.completions.create(**params)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        content = resp.choices[0].message.content or ""
    except Exception:  # noqa: BLE001
        content = ""
    return {"choices": [{"message": {"content": content}}]}


@router.post("/items/extract")
async def extract_items(req: ExtractRequest, db: AsyncSession = Depends(get_db)):
    """调用大模型从对话中提取标的物，返回 OpenAI 兼容格式。"""
    logger.info(f"Extracting items for conversation_id={req.conversation_id}, model={req.model}")
    
    # 1. 从 DB 获取历史消息
    history_msgs = await crud_messages.list_messages(
        db=db, conversation_id=req.conversation_id, limit=200
    )
    
    conversation_summary = "\n\n".join(
        [
            f"{'用户' if m.role == 'user' else 'AI'}: {m.content}"
            for m in history_msgs
        ]
    )

    prompt = (
        "请从以下对话内容中提取所有产品型号/标的物信息。\n\n"
        f"{conversation_summary}\n\n"
        "请以 JSON 数组格式返回提取的产品型号，每个元素包含：\n"
        "- name: 产品型号名称（必填）\n"
        "- quantity: 数量（如有）\n\n"
        "只返回 JSON 数组，不要包含任何其他文字。"
    )

    params: Dict[str, Any] = {
        "model": req.model or settings.LLM_DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    client = _get_client()
    try:
        resp = await client.chat.completions.create(**params)
        content = resp.choices[0].message.content or "[]"
        logger.info(f"Extracted items: {content}")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Error extracting items: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse({"choices": [{"message": {"content": content}}]})


def _ts_to_dt(ts: Optional[int]) -> datetime:
    if ts is None:
        return datetime.utcnow()
    return datetime.fromtimestamp(ts / 1000)


@router.post("/conversations/sync", response_model=ConversationOut)
async def sync_conversation(
    req: ConversationSyncRequest, db: AsyncSession = Depends(get_db)
):
    """按 id 同步会话及消息。"""
    logger.info(f"Syncing conversation: id={req.id}, title={req.title}")
    conv: Conversation | None = None
    if req.id:
        conv = await crud_conversations.get(db, req.id)
    if conv is None:
        logger.info(f"Creating new conversation: title={req.title}")
        conv = await crud_conversations.create(
            db,
            obj_in={
                "name": req.title or "新对话",
                "first_user_message": req.title or "",
                "status": "active",
                "created_at": _ts_to_dt(req.created_at),
                "updated_at": _ts_to_dt(req.updated_at),
            },
        )
        await db.flush()
    else:
        logger.info(f"Updating existing conversation: id={conv.id}")
        await crud_conversations.update_by_id(
            db,
            conv.id,
            {
                "updated_at": _ts_to_dt(req.updated_at) if req.updated_at else datetime.utcnow(),
            },
        )

    # 同步单条消息（用户提问或大模型回答）
    if req.message:
        logger.info(f"Syncing message: role={req.message.role}, content={req.message.content[:100]}")
        await crud_messages.create(
            db,
            obj_in={
                "conversation_id": conv.id,
                "role": req.message.role,
                "content": req.message.content,
                "created_at": _ts_to_dt(req.message.timestamp),
                "deep_thinking": req.message.deep_thinking,
                "model": req.message.model,
            },
        )

    await db.commit()
    await db.refresh(conv)

    return ConversationOut(
        id=conv.id,
        title=conv.name,
        created_at=int(conv.created_at.timestamp() * 1000),
        updated_at=int(conv.updated_at.timestamp() * 1000),
    )


@router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    convs = await crud_conversations.list_conversations(db, limit=200, offset=0)
    return [
        ConversationOut(
            id=c.id,
            title=c.name,
            created_at=int(c.created_at.timestamp() * 1000),
            updated_at=int(c.updated_at.timestamp() * 1000),
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
async def list_conversation_messages(conversation_id: int, db: AsyncSession = Depends(get_db)):
    conv = await crud_conversations.get(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = await crud_messages.list_messages(db, conversation_id=conv.id, limit=500)
    return [
        MessageOut(
            id=str(m.id),
            role=m.role,
            content=m.content,
            timestamp=int(m.created_at.timestamp() * 1000),
            deep_thinking=m.deep_thinking,
            model=m.model,
        )
        for m in msgs
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    conv = await crud_conversations.get(db, conversation_id)
    if not conv:
        return {"success": True}
    await crud_messages.delete_by_conversation(db, conv.id)
    await crud_conversations.delete_by_id(db, conv.id)
    await db.commit()
    return {"success": True}

