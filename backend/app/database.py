"""数据库连接与会话管理"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# 确保数据库目录存在
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


async def seed_default_skills():
    """启动时 seed 默认技能（幂等）"""
    from app.models.skill import Skill
    from app.config import settings
    from sqlalchemy import select
    from pathlib import Path
    import uuid

    async with async_session() as db:
        # 检查 hub-connect 是否已存在
        result = await db.execute(
            select(Skill).where(Skill.skill_name == "hub-connect", Skill.is_deleted == 0)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return

        # 读取 SKILL.md
        skill_path = Path(__file__).parent / "skills" / "hub-connect" / "1.0.0" / "SKILL.md"
        if not skill_path.exists():
            return

        content = skill_path.read_text(encoding="utf-8")

        # 创建技能记录
        skill = Skill(
            id=str(uuid.uuid4()),
            skill_name="hub-connect",
            display_name="中台接入技能",
            description="引导 Agent 对话式接入 Agent Hub 智能体中台",
            category="system",
            version="1.0.0",
            scope="public",
            source="system",
            is_mandatory=1,
            security_status="passed",
            security_risk_level="none",
        )
        db.add(skill)

        # 保存文件到 skills 存储目录
        target_dir = Path(settings.skills_dir) / "hub-connect" / "1.0.0"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "SKILL.md").write_text(content, encoding="utf-8")

        await db.commit()
        print("✅ hub-connect 预置技能已创建")
