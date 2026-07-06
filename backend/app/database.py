"""数据库连接与会话管理"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# 确保数据库目录存在
import os
_db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
_db_dir = os.path.dirname(_db_path)
if _db_dir and not os.path.exists(_db_dir):
    os.makedirs(_db_dir, exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """创建所有表（开发环境 SQLite 自动建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_wal_mode():
    """SQLite WAL 模式 + busy_timeout"""
    async with engine.connect() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.exec_driver_sql("PRAGMA busy_timeout=5000;")
