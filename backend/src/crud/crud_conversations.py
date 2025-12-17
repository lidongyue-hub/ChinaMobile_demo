from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.base import CRUDBase
from src.db.models import Conversation
from datetime import datetime


class CRUDConversations(CRUDBase[Conversation]):
    async def list_conversations(
        self, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        result = await db.execute(
            select(Conversation)
            .order_by(Conversation.pinned.desc(), Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_name(
        self, db: AsyncSession, conversation_id: int, name: str
    ) -> None:
        await self.update_by_id(
            db,
            conversation_id,
            {"name": name, "updated_at": datetime.utcnow()},
        )

    async def touch_updated_at(
        self, db: AsyncSession, conversation_id: int
    ) -> None:
        await self.update_by_id(
            db, conversation_id, {"updated_at": datetime.utcnow()}
        )

    async def delete_conversation(self, db: AsyncSession, conversation_id: int) -> None:
        await self.delete_by_id(db, conversation_id)


crud_conversations = CRUDConversations(Conversation)

