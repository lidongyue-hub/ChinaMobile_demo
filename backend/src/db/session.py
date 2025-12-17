from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=200,
    max_overflow=100,
    pool_timeout=65,
    pool_recycle=3600 * 4,
)


# 确保 MySQL 连接使用上海时区（UTC+8）
@event.listens_for(engine.sync_engine, "connect")
def _set_timezone(dbapi_connection, connection_record):  # pragma: no cover - 连接钩子
    with dbapi_connection.cursor() as cursor:
        cursor.execute("SET time_zone = '+08:00'")

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncSession:
    """FastAPI 依赖：获取一个异步数据库会话。"""
    async with AsyncSessionLocal() as session:
        yield session

