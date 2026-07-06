"""审计日志服务"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        actor: str,
        target: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """记录审计日志"""
        entry = AuditLog(
            id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            target=target,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.commit()
        return entry

    async def list_logs(
        self,
        action: str | None = None,
        actor: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """查询审计日志"""
        query = select(AuditLog).order_by(desc(AuditLog.created_at))
        count_stmt = select(func.count(AuditLog.id))

        if action:
            query = query.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)
        if actor:
            query = query.where(AuditLog.actor == actor)
            count_stmt = count_stmt.where(AuditLog.actor == actor)

        # 总数
        total = await self.db.scalar(count_stmt) or 0

        # 分页
        result = await self.db.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all()), total

    async def get_stats(self) -> dict:
        """审计统计"""
        # 最近 24 小时操作数
        day_ago = datetime.now(timezone.utc)
        stmt = select(func.count(AuditLog.id)).where(
            AuditLog.created_at >= day_ago
        )
        recent = await self.db.scalar(stmt) or 0

        # 操作类型分布
        stmt = select(AuditLog.action, func.count(AuditLog.id).label("cnt")).group_by(AuditLog.action)
        result = await self.db.execute(stmt)
        actions = {row[0]: row[1] for row in result}

        return {
            "total_logs": await self.db.scalar(select(func.count(AuditLog.id))) or 0,
            "recent_24h": recent,
            "action_distribution": actions,
        }
