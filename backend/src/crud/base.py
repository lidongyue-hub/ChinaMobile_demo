from typing import Any, Dict, Generic, Optional, Type, TypeVar

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """通用 CRUD 基类，提供基础的 get/create/update 能力。"""

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, obj_id: int) -> Optional[ModelType]:
        return await db.get(self.model, obj_id)

    async def create(
        self, db: AsyncSession, *, obj_in: Dict[str, Any]
    ) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update_by_id(
        self, db: AsyncSession, obj_id: int, values: Dict[str, Any]
    ) -> None:
        await db.execute(
            update(self.model).where(self.model.id == obj_id).values(**values)
        )

    async def delete_by_id(self, db: AsyncSession, obj_id: int) -> None:
        await db.execute(delete(self.model).where(self.model.id == obj_id))

