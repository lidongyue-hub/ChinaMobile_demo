from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from fastapi import Form


class ConversationCreateRequest(BaseModel):
    message: str
    name: Optional[str] = None
    model: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        message: str = Form(...),
        name: Optional[str] = Form(None),
        model: Optional[str] = Form(None),
    ) -> "ConversationCreateRequest":
        return cls(message=message, name=name, model=model)

class ConversationMessageRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str
    model: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        conversation_id: Optional[int] = Form(None),
        message: str = Form(...),
        model: Optional[str] = Form(None),
    ) -> "ConversationMessageRequest":
        return cls(
            conversation_id=conversation_id,
            message=message,
            model=model,
        )

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    file_path: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    name: str
    first_user_message: Optional[str] = None
    status: str
    pinned: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]


class ChatReplyResponse(BaseModel):
    conversation: ConversationResponse
    assistant_message: MessageResponse
    thought: Optional[str] = None


class ConversationRenameRequest(BaseModel):
    name: str


class ConversationPinRequest(BaseModel):
    pinned: bool


