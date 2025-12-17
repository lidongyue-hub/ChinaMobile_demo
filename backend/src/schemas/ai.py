from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    message: str
    conversation_id: Optional[int] = None
    # 生成参数统一由后端 settings 管理


class ExtractRequest(BaseModel):
    conversation_id: int
    model: Optional[str] = None


class ConversationMessageIn(BaseModel):
    role: str
    content: str
    timestamp: Optional[int] = None
    message_id: Optional[str] = None
    deep_thinking: Optional[str] = None
    model: Optional[str] = None


class ConversationSyncRequest(BaseModel):
    id: Optional[int] = None
    title: str
    message: Optional[ConversationMessageIn] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: int
    updated_at: int


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    timestamp: int
    deep_thinking: Optional[str] = None
    model: Optional[str] = None


