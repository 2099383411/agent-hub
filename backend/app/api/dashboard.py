"""仪表盘 API"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent, AgentStatus
from app.models.skill import Skill
from app.models.agent_skill import AgentSkill, AgentSkillStatus
from app.schemas.common import ApiResponse
from app.api.auth import verify_admin

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin),
):
    # Agent 统计
    total_agents = await db.scalar(select(func.count(Agent.id)).where(Agent.is_deleted == 0))
    online_agents = await db.scalar(
        select(func.count(Agent.id)).where(Agent.is_deleted == 0, Agent.status == AgentStatus.ONLINE.value)
    )

    # 技能统计
    total_skills = await db.scalar(select(func.count(Skill.id)).where(Skill.is_deleted == 0, Skill.is_active == 1))
    mandatory_skills = await db.scalar(
        select(func.count(Skill.id)).where(Skill.is_deleted == 0, Skill.is_mandatory == 1)
    )

    # 合规统计
    total_agents_val = total_agents or 0
    compliant_count = 0
    from app.services.compliance_service import ComplianceService
    results = await ComplianceService(db).get_global_compliance()
    compliant_count = sum(1 for r in results if r["status"] == "compliant")
    non_compliant = total_agents_val - compliant_count

    # 安全统计
    high_risk = await db.scalar(
        select(func.count(Skill.id)).where(
            Skill.is_deleted == 0, Skill.security_risk_level == "high", Skill.is_blocked == 0
        )
    )

    return ApiResponse(data={
        "agents": {
            "total": total_agents_val,
            "online": online_agents or 0,
            "offline": total_agents_val - (online_agents or 0),
        },
        "skills": {
            "total": total_skills or 0,
            "mandatory": mandatory_skills or 0,
        },
        "compliance": {
            "compliant": compliant_count,
            "non_compliant": non_compliant,
            "compliance_rate": round(compliant_count / total_agents_val * 100, 1) if total_agents_val > 0 else 100.0,
        },
        "security": {
            "high_risk_skills": high_risk or 0,
        },
    })
