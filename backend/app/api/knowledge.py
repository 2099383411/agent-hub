"""知识库 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.knowledge_service import KnowledgeService
from app.services.audit_service import AuditService
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("")
async def list_knowledge(
    category: str = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = KnowledgeService(db)
    entries = await service.list_all(category)
    return ApiResponse(data=[{
        "id": e.id,
        "title": e.title,
        "category": e.category,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    } for e in entries])


@router.post("")
async def create_knowledge(
    data: KnowledgeCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = KnowledgeService(db)
    entry = await service.create(data)
    await AuditService(db).log("knowledge.create", "admin", data.title)
    return ApiResponse(data={
        "id": entry.id,
        "title": entry.title,
        "category": entry.category,
    })


@router.get("/{entry_id}")
async def get_knowledge(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = KnowledgeService(db)
    entry = await service.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return ApiResponse(data=entry.model_dump())


@router.put("/{entry_id}")
async def update_knowledge(
    entry_id: str,
    data: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = KnowledgeService(db)
    entry = await service.update(entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return ApiResponse(data={"updated": True})


@router.delete("/{entry_id}")
async def delete_knowledge(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = KnowledgeService(db)
    entry = await service.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    ok = await service.delete(entry_id)
    await AuditService(db).log("knowledge.delete", "admin", entry.title)
    return ApiResponse(data={"deleted": True})
