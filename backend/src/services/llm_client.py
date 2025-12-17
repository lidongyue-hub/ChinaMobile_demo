import logging
from typing import Dict, List

from openai import AsyncOpenAI

from src.config import settings

logger = logging.getLogger(__name__)



class LLMError(Exception):
    """调用底层大模型(LLM) 接口异常。"""


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """懒加载 OpenAI 兼容客户端，可通过 LLM_BASE_URL 指向 DeepSeek 等服务。"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
    return _client


async def chat(
    messages: List[Dict[str, str]],
    model: str | None = None,
    response_format: str | None = None,
) -> str:
    """调用 OpenAI 兼容 Chat Completion 接口，返回回复文本。

    messages: 形如 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    model: 具体使用的大模型名称，若为 None 则使用 settings.LLM_DEFAULT_MODEL。
    """
    if not settings.LLM_API_KEY:
        raise LLMError("LLM_API_KEY 未配置")

    client = _get_client()

    resolved_model = model or settings.LLM_DEFAULT_MODEL
    if not resolved_model:
        raise LLMError("未配置模型名称，请设置 model 或 LLM_DEFAULT_MODEL")

    params: Dict = {
        "model": resolved_model,
        "messages": messages,
    }
    if response_format:
        # OpenAI v1 客户端支持 response_format={"type": "json_object"} 等
        params["response_format"] = {"type": response_format}

    try:
        logger.info(f"Calling LLM: model={resolved_model}, messages: {messages}")
        resp = await client.chat.completions.create(**params)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"LLM API call failed: {exc}", exc_info=True)
        raise LLMError(f"LLM 调用失败: {exc}") from exc

    try:
        content = resp.choices[0].message.content or ""
        logger.info(f"LLM response received, content: {content}")
    except (AttributeError, IndexError) as exc:  # pragma: no cover - 防御性
        logger.error(f"Failed to parse LLM response: {resp}", exc_info=True)
        raise LLMError(f"Unexpected LLM response: {resp}") from exc

    return content


