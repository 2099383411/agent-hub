"""审计日志 API"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.audit_service import AuditService
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit"])


@router.get("")
async def list_logs(
    action: str = None,
    actor: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = AuditService(db)
    offset = (page - 1) * page_size
    logs, total = await service.list_logs(action, actor, page_size, offset)
    return ApiResponse(data={
        "items": [{
            "id": log.id,
            "action": log.action,
            "actor": log.actor,
            "target": log.target,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        } for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/stats")
async def log_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = AuditService(db)
    stats = await service.get_stats()
    return ApiResponse(data=stats)
