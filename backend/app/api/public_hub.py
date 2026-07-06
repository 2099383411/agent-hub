"""公共平台 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.public_hub_service import PublicHubService
from app.services.audit_service import AuditService
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin

router = APIRouter(prefix="/api/v1/public-hub", tags=["public-hub"])


@router.get("/search")
async def search_hub(
    q: str,
    source: str = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = PublicHubService(db)
    results = await service.search(q, source)
    return ApiResponse(data={"results": results, "total": len(results)})


@router.post("/import")
async def import_skill(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    name = data.get("name")
    source = data.get("source")
    source_url = data.get("source_url")

    if not name or not source:
        raise HTTPException(status_code=400, detail="name 和 source 为必填")

    service = PublicHubService(db)
    try:
        result = await service.import_skill(name, source, source_url)
        await AuditService(db).log("skill.import", "admin", name, f"source={source}")
        return ApiResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
