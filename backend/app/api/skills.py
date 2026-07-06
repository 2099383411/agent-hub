"""技能管理 API"""

import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.skill_service import SkillService
from app.services.security_service import SecurityService
from app.services.audit_service import AuditService
from app.schemas.skill import (
    SkillCreate, SkillAssignRequest, SkillScopeUpdate,
    SkillUploadResponse, SkillListItem,
)
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin
from app.models.skill import Skill
from app.config import settings
from pathlib import Path

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("")
async def list_skills(
    category: str = None,
    scope: str = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SkillService(db)
    skills = await service.list_skills(category=category, scope=scope, include_blocked=True)
    return ApiResponse(data={"skills": [s.model_dump() for s in skills], "total": len(skills)})


@router.post("/upload")
async def upload_skill(
    file: UploadFile = File(...),
    scope: str = Form("private"),
    is_mandatory: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    """上传技能文件 → 自动进安检"""
    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    # 解析技能名
    skill_name = file.filename.replace(".md", "").replace(".yaml", "").replace(".yml", "") if file.filename else f"skill_{uuid.uuid4().hex[:8]}"

    # 创建技能记录
    skill = Skill(
        id=str(uuid.uuid4()),
        skill_name=skill_name,
        display_name=skill_name,
        version="1.0.0",
        scope=scope,
        source="upload",
        is_mandatory=1 if is_mandatory else 0,
    )
    db.add(skill)
    await db.commit()

    # 保存文件
    skill_dir = Path(settings.skills_dir) / skill_name / "1.0.0"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(text_content, encoding="utf-8")

    # 自动触发 Tier 1 静态分析
    security_service = SecurityService(db)
    scan = await security_service.run_static_analysis(skill.id, text_content)

    await db.refresh(skill)
    await AuditService(db).log("skill.upload", "admin", skill_name, f"risk={skill.security_risk_level}")

    return ApiResponse(data=SkillUploadResponse(
        id=skill.id,
        skill_name=skill.skill_name,
        version=skill.version,
        security_status=skill.security_status,
        security_risk_level=skill.security_risk_level,
        message=f"技能已上传并完成静态分析，发现 {len(json.loads(scan.findings or '[]'))} 个风险项",
    ))


@router.get("/{skill_id}")
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    skill = await db.get(Skill, skill_id)
    if not skill or skill.is_deleted:
        raise HTTPException(status_code=404, detail="技能不存在")
    return ApiResponse(data=SkillListItem(
        name=skill.skill_name,
        version=skill.version,
        display_name=skill.display_name,
        description=skill.description,
        category=skill.category,
        scope=skill.scope,
        security_status=skill.security_status,
        security_risk_level=skill.security_risk_level,
        is_mandatory=bool(skill.is_mandatory),
    ).model_dump())


@router.post("/{skill_id}/assign")
async def assign_skill(
    skill_id: str,
    data: SkillAssignRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SkillService(db)
    await service.assign_skill(skill_id, data.agent_ids)
    await AuditService(db).log("skill.assign", "admin", f"skill={skill_id}", f"agents={data.agent_ids}")
    return ApiResponse(data={"assigned": True})


@router.post("/{skill_id}/unassign")
async def unassign_skill(
    skill_id: str,
    data: SkillAssignRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SkillService(db)
    await service.unassign_skill(skill_id, data.agent_ids)
    await AuditService(db).log("skill.unassign", "admin", f"skill={skill_id}", f"agents={data.agent_ids}")
    return ApiResponse(data={"unassigned": True})


@router.put("/{skill_id}")
async def update_skill(
    skill_id: str,
    data: SkillScopeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SkillService(db)
    await service.update_scope(skill_id, data.scope, data.is_mandatory)
    return ApiResponse(data={"updated": True})


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    skill = await db.get(Skill, skill_id)
    if skill:
        skill.is_deleted = 1
        await db.commit()
    await AuditService(db).log("skill.delete", "admin", skill.skill_name if skill else skill_id)
    return ApiResponse(data={"deleted": True})


@router.post("/{skill_id}/block")
async def block_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    service = SkillService(db)
    await service.block_skill(skill_id)
    await AuditService(db).log("skill.block", "admin", skill_id)
    return ApiResponse(data={"blocked": True})
