from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.base import CRUDBase
from src.db.models import Message


class CRUDMessages(CRUDBase[Message]):
    async def create_message(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        role: str,
        content: str,
        deep_thinking: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Message:
        return await self.create(
            db,
            obj_in={
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "deep_thinking": deep_thinking,
                "model": model,
            },
        )

    async def list_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_recent_for_context(
        self, db: AsyncSession, *, conversation_id: int, limit: int = 10
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())[::-1]

    async def delete_by_conversation(
        self, db: AsyncSession, conversation_id: int
    ) -> None:
        await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )


crud_messages = CRUDMessages(Message)

