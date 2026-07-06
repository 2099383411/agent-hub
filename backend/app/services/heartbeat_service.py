"""心跳服务"""

import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.agent_skill import AgentSkill, AgentSkillStatus
from app.models.skill import Skill
from app.models.compliance_check import ComplianceCheck
from app.models.tool import Tool
from app.schemas.heartbeat import (
    HeartbeatRequest, HeartbeatResponse,
    PendingSkill, OutdatedSkill, ComplianceStatus,
)
from app.services.compliance_service import ComplianceService
from app.services.agent_service import AgentService

from packaging.version import Version


class HeartbeatService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_service = AgentService(db)
        self.compliance_service = ComplianceService(db)

    async def process_heartbeat(self, app_id: str, data: HeartbeatRequest) -> HeartbeatResponse:
        """处理 Agent 心跳"""
        agent = await self.agent_service.get_agent_by_app_id(app_id)
        if not agent:
            return HeartbeatResponse(status="error", compliance=ComplianceStatus(status="unknown"))

        # 更新 Agent 状态
        await self.agent_service.update_heartbeat(
            agent,
            host_ip=data.agent_info.host_ip,
            version=data.agent_info.version,
        )

        # 1. 更新已安装技能状态
        for installed in data.installed_skills:
            skill = await self.db.execute(
                select(Skill).where(Skill.skill_name == installed.name, Skill.is_deleted == 0)
            )
            skill = skill.scalar_one_or_none()
            if skill:
                ag_sk = await self.db.execute(
                    select(AgentSkill).where(
                        AgentSkill.agent_id == agent.id,
                        AgentSkill.skill_id == skill.id,
                    )
                )
                ag_sk = ag_sk.scalar_one_or_none()
                if ag_sk:
                    ag_sk.status = AgentSkillStatus.INSTALLED
                    ag_sk.installed_version = installed.version
                    ag_sk.installed_at = datetime.now(timezone.utc)

        # 2. 更新工具发现
        for tool_info in data.available_tools:
            existing = await self.db.execute(
                select(Tool).where(
                    Tool.agent_id == agent.id,
                    Tool.tool_name == tool_info.name,
                )
            )
            if not existing.scalar_one_or_none():
                tool = Tool(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    tool_name=tool_info.name,
                    tool_version=tool_info.version,
                    tool_path=tool_info.path,
                )
                self.db.add(tool)

        await self.db.commit()

        # 3. 计算 pending_skills
        pending = []
        ag_skills = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent.id,
                AgentSkill.status == AgentSkillStatus.PENDING,
            )
        )
        for ag_sk in ag_skills.scalars():
            skill = await self.db.get(Skill, ag_sk.skill_id)
            if skill and not skill.is_blocked:
                pending.append(PendingSkill(
                    name=skill.skill_name,
                    version=skill.version,
                    mandatory=bool(skill.is_mandatory),
                    assigned_at=ag_sk.assigned_at.isoformat() if ag_sk.assigned_at else None,
                    scope=skill.scope,
                ))

        # 4. 计算 outdated_skills
        outdated = []
        for installed in data.installed_skills:
            skill = await self.db.execute(
                select(Skill).where(Skill.skill_name == installed.name, Skill.is_deleted == 0)
            )
            skill = skill.scalar_one_or_none()
            if skill and skill.version != installed.version:
                try:
                    if Version(skill.version) > Version(installed.version):
                        outdated.append(OutdatedSkill(
                            name=installed.name,
                            current_version=skill.version,
                            installed_version=installed.version,
                            update_urgency="recommended",
                        ))
                except Exception:
                    pass

        # 5. 合规检查
        compliance = await self.compliance_service.check_compliance(agent.id)

        # 记录合规检查
        cc = ComplianceCheck(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            status=compliance.status,
            missing_skills=json.dumps(compliance.missing_mandatory, ensure_ascii=False),
        )
        self.db.add(cc)
        await self.db.commit()

        return HeartbeatResponse(
            status="ok",
            last_heartbeat_at=datetime.now(timezone.utc).isoformat(),
            pending_skills=pending,
            outdated_skills=outdated,
            compliance=compliance,
        )
