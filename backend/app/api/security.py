"""安全检测 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.security_service import SecurityService
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin

router = APIRouter(prefix="/api/v1/security", tags=["security"])


@router.get("/scans")
async def list_scans(
    skill_id: str = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SecurityService(db)
    scans = await service.get_scans(skill_id)
    results = []
    for scan in scans:
        import json
        results.append({
            "id": scan.id,
            "skill_id": scan.skill_id,
            "scan_type": scan.scan_type,
            "risk_level": scan.risk_level,
            "status": scan.status,
            "findings": json.loads(scan.findings) if scan.findings else [],
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        })
    return ApiResponse(data=results)


@router.get("/scans/{scan_id}")
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SecurityService(db)
    scan = await service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="扫描记录不存在")
    import json
    return ApiResponse(data={
        "id": scan.id,
        "skill_id": scan.skill_id,
        "scan_type": scan.scan_type,
        "risk_level": scan.risk_level,
        "status": scan.status,
        "findings": json.loads(scan.findings) if scan.findings else [],
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    })


@router.put("/policy")
async def update_policy(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    from app.models.system_config import SystemConfig
    from sqlalchemy import select

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "security_policy")
    )
    config = result.scalar_one_or_none()
    if not config:
        config = SystemConfig(config_key="security_policy", config_value=json.dumps(data))
        db.add(config)
    else:
        config.config_value = json.dumps(data)
    await db.commit()
    return ApiResponse(data={"updated": True})
