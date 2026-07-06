"""合规检查 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.compliance_service import ComplianceService
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin
from app.models.system_config import SystemConfig
from sqlalchemy import select
import json

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/status")
async def global_compliance(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = ComplianceService(db)
    results = await service.get_global_compliance()
    return ApiResponse(data=results)


@router.get("/mandatory")
async def get_mandatory(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    from app.models.skill import Skill
    from sqlalchemy import select as sql_select
    result = await db.execute(
        sql_select(Skill).where(Skill.is_mandatory == 1, Skill.is_deleted == 0)
    )
    skills = [{"id": s.id, "name": s.skill_name, "version": s.version} for s in result.scalars()]
    return ApiResponse(data=skills)


@router.put("/mandatory")
async def update_mandatory(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    action = data.get("action")
    skill_id = data.get("skill_id")
    if action == "add" and skill_id:
        from app.models.skill import Skill
        skill = await db.get(Skill, skill_id)
        if skill:
            skill.is_mandatory = 1
            await db.commit()
    elif action == "remove" and skill_id:
        skill = await db.get(Skill, skill_id)
        if skill:
            skill.is_mandatory = 0
            await db.commit()
    return ApiResponse(data={"updated": True})
