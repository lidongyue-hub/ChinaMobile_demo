from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


SHANGHAI_TZ = timezone(timedelta(hours=8))


def now_shanghai() -> datetime:
    """返回上海时区的当前时间（去除 tzinfo，便于入库 DATETIME）。"""
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)


class Base(DeclarativeBase):
    """SQLAlchemy ORM 基类。"""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai, onupdate=now_shanghai
    )


class Conversation(Base):
    """会话表：记录会话名称、首条用户问题等。"""

    __tablename__ = "conversations"

    name: Mapped[str] = mapped_column(String(255))
    first_user_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)

    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    """消息表：会话内的历史对话记录。"""

    __tablename__ = "messages"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user / assistant / system
    content: Mapped[str] = mapped_column(Text)
    deep_thinking: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
