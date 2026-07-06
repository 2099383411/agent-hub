"""知识库服务"""

import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_entry import KnowledgeEntry
from app.schemas.knowledge import (
    KnowledgeSearchResult, KnowledgeSearchResponse,
    KnowledgeGetResponse, KnowledgeCreate, KnowledgeUpdate,
)


class KnowledgeService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str, category: str | None = None) -> KnowledgeSearchResponse:
        """搜索知识库（简单 LIKE 搜索）"""
        conditions = [KnowledgeEntry.is_deleted == 0]
        if category:
            conditions.append(KnowledgeEntry.category == category)

        like_pattern = f"%{query}%"
        conditions.append(
            or_(
                KnowledgeEntry.title.ilike(like_pattern),
                KnowledgeEntry.content.ilike(like_pattern),
            )
        )

        stmt = select(KnowledgeEntry).where(*conditions).order_by(KnowledgeEntry.created_at.desc())
        result = await self.db.execute(stmt)
        entries = list(result.scalars().all())

        items = []
        for entry in entries:
            snippet = entry.content[:200] if entry.content else ""
            # 尝试定位匹配位置
            if query.lower() in entry.content.lower():
                idx = entry.content.lower().index(query.lower())
                start = max(0, idx - 50)
                snippet = ("..." if start > 0 else "") + entry.content[start:start + 200] + ("..." if len(entry.content) > start + 200 else "")

            items.append(KnowledgeSearchResult(
                id=entry.id,
                title=entry.title,
                category=entry.category,
                snippet=snippet,
                relevance=1.0 if query.lower() in entry.title.lower() else 0.5,
                updated_at=entry.updated_at,
            ))

        return KnowledgeSearchResponse(results=items, total=len(items))

    async def get(self, entry_id: str) -> KnowledgeGetResponse | None:
        entry = await self.db.get(KnowledgeEntry, entry_id)
        if not entry or entry.is_deleted:
            return None
        return KnowledgeGetResponse(
            id=entry.id,
            title=entry.title,
            content=entry.content,
            category=entry.category,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )

    async def create(self, data: KnowledgeCreate) -> KnowledgeEntry:
        entry = KnowledgeEntry(
            id=str(uuid.uuid4()),
            title=data.title,
            content=data.content,
            category=data.category,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def update(self, entry_id: str, data: KnowledgeUpdate) -> KnowledgeEntry | None:
        entry = await self.db.get(KnowledgeEntry, entry_id)
        if not entry or entry.is_deleted:
            return None
        if data.title is not None:
            entry.title = data.title
        if data.content is not None:
            entry.content = data.content
        if data.category is not None:
            entry.category = data.category
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete(self, entry_id: str) -> bool:
        entry = await self.db.get(KnowledgeEntry, entry_id)
        if not entry:
            return False
        entry.is_deleted = 1
        await self.db.commit()
        return True

    async def list_all(self, category: str | None = None) -> list[KnowledgeEntry]:
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.is_deleted == 0)
        if category:
            stmt = stmt.where(KnowledgeEntry.category == category)
        stmt = stmt.order_by(KnowledgeEntry.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
