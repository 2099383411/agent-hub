"""合规检查服务"""

import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.models.agent_skill import AgentSkill, AgentSkillStatus
from app.schemas.heartbeat import ComplianceStatus


class ComplianceService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_compliance(self, agent_id: str) -> ComplianceStatus:
        """检查 Agent 是否满足必装技能要求"""
        # 获取所有必装技能
        result = await self.db.execute(
            select(Skill).where(Skill.is_mandatory == 1, Skill.is_deleted == 0, Skill.is_blocked == 0)
        )
        mandatory_skills = list(result.scalars().all())

        # 获取 Agent 已安装的技能
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent_id,
                AgentSkill.status.in_([AgentSkillStatus.INSTALLED, AgentSkillStatus.OUTDATED]),
            )
        )
        installed = {as_.skill_id for as_ in result.scalars()}

        missing = []
        for sk in mandatory_skills:
            if sk.id not in installed:
                missing.append(sk.skill_name)

        status = "non_compliant" if missing else "compliant"

        return ComplianceStatus(
            status=status,
            missing_mandatory=missing,
            total_mandatory=len(mandatory_skills),
            installed_mandatory=len(mandatory_skills) - len(missing),
        )

    async def get_global_compliance(self) -> list[dict]:
        """获取所有 Agent 的合规状态"""
        from app.models.agent import Agent
        result = await self.db.execute(
            select(Agent).where(Agent.is_deleted == 0)
        )
        agents = list(result.scalars().all())

        results = []
        for agent in agents:
            compliance = await self.check_compliance(agent.id)
            results.append({
                "agent_id": agent.id,
                "agent_name": agent.agent_name,
                "status": compliance.status,
                "missing_mandatory": compliance.missing_mandatory,
            })

        return results
