"""系统相关 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, init_db, init_wal_mode
from app.models.system_config import SystemConfig
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin
from app.config import settings
import time

router = APIRouter(prefix="/api/v1/system", tags=["system"])

_start_time = time.time()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """健康检查"""
    try:
        await db.execute(select(SystemConfig).limit(1))
        db_status = "connected"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy",
        "db": db_status,
        "uptime_seconds": int(time.time() - _start_time),
        "version": settings.app_version,
    }


@router.get("/onboarding")
async def get_onboarding(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "onboarding_content")
    )
    config = result.scalar_one_or_none()
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "onboarding_version")
    )
    ver = result.scalar_one_or_none()
    return ApiResponse(data={
        "version": int(ver.config_value) if ver else 1,
        "content": config.config_value if config else "",
        "updated_at": config.updated_at.isoformat() if config else None,
    })


@router.put("/onboarding")
async def update_onboarding(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    content = data.get("content", "")

    # 更新内容
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "onboarding_content")
    )
    config = result.scalar_one_or_none()
    if not config:
        config = SystemConfig(config_key="onboarding_content", config_value=content)
        db.add(config)
    else:
        config.config_value = content

    # 递增版本号
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "onboarding_version")
    )
    ver = result.scalar_one_or_none()
    if not ver:
        ver = SystemConfig(config_key="onboarding_version", config_value="1")
        db.add(ver)
    else:
        ver.config_value = str(int(ver.config_value) + 1)

    await db.commit()
    return ApiResponse(data={"version": int(ver.config_value), "updated": True})
