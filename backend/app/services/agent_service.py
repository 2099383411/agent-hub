"""Agent 管理服务"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus
from app.models.agent_skill import AgentSkill
from app.schemas.agent import AgentCreate
from app.utils.security import hash_password, generate_app_credentials, generate_onboard_token


class AgentService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(self, data: AgentCreate) -> tuple[Agent, str, str, str]:
        """创建 Agent，返回 (agent, app_secret, onboard_token, onboard_command)"""
        app_id, app_secret = generate_app_credentials()
        onboard_token, onboard_expires = generate_onboard_token()

        agent = Agent(
            id=str(uuid.uuid4()),
            agent_name=data.agent_name,
            agent_type=data.agent_type or "generic",
            app_id=app_id,
            app_secret_hash=hash_password(app_secret),
            onboard_token=onboard_token,
            onboard_token_expires_at=onboard_expires,
            host_ip=data.host_ip,
            version=data.version,
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)

        # 构造一键命令
        from app.config import get_public_url
        public_url = get_public_url()
        onboard_cmd = f"curl -s {public_url}/api/v1/onboard/claim?token={onboard_token} | bash"

        return agent, app_secret, onboard_token, onboard_cmd

    async def get_agent(self, agent_id: str) -> Agent | None:
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.is_deleted == 0)
        )
        return result.scalar_one_or_none()

    async def get_agent_by_app_id(self, app_id: str) -> Agent | None:
        result = await self.db.execute(
            select(Agent).where(Agent.app_id == app_id, Agent.is_deleted == 0)
        )
        return result.scalar_one_or_none()

    async def get_agent_by_onboard_token(self, token: str) -> Agent | None:
        result = await self.db.execute(
            select(Agent).where(Agent.onboard_token == token, Agent.is_deleted == 0)
        )
        return result.scalar_one_or_none()

    async def list_agents(self) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.is_deleted == 0).order_by(Agent.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_agent(self, agent_id: str) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        agent.is_deleted = 1
        await self.db.commit()
        return True

    async def update_heartbeat(self, agent: Agent, host_ip: str | None, version: str | None):
        agent.status = AgentStatus.ONLINE.value
        agent.last_heartbeat_at = datetime.now(timezone.utc)
        if host_ip:
            agent.host_ip = host_ip
        if version:
            agent.version = version
        await self.db.commit()

    async def mark_offline(self):
        """标记长时间未心跳的 Agent 为离线"""
        timeout = datetime.now(timezone.utc)
        stmt = select(Agent).where(
            Agent.is_deleted == 0,
            Agent.status == AgentStatus.ONLINE.value,
            Agent.last_heartbeat_at.isnot(None),
        )
        result = await self.db.execute(stmt)
        for agent in result.scalars():
            if agent.last_heartbeat_at:
                diff = (datetime.now(timezone.utc) - agent.last_heartbeat_at.replace(tzinfo=timezone.utc)).total_seconds()
                if diff > 300:  # 5 分钟
                    agent.status = AgentStatus.OFFLINE.value
        await self.db.commit()

    async def get_agent_installed_skills(self, agent_id: str) -> list[dict]:
        """获取 Agent 已安装技能列表"""
        from app.models.skill import Skill
        stmt = select(AgentSkill, Skill).join(
            Skill, AgentSkill.skill_id == Skill.id
        ).where(
            AgentSkill.agent_id == agent_id,
            AgentSkill.status.in_(["installed", "outdated"]),
        )
        result = await self.db.execute(stmt)
        skills = []
        for ag_sk, sk in result:
            skills.append({
                "name": sk.skill_name,
                "version": ag_sk.installed_version or sk.version,
                "latest_version": sk.version,
                "status": ag_sk.status,
            })
        return skills

    async def refresh_onboard_token(self, agent_id: str) -> tuple[str, str]:
        """为已存在的 Agent 重新生成 onboard token"""
        from app.utils.security import generate_onboard_token
        from app.config import get_public_url

        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent 不存在")

        onboard_token, onboard_expires = generate_onboard_token()
        agent.onboard_token = onboard_token
        agent.onboard_token_expires_at = onboard_expires
        await self.db.commit()

        public_url = get_public_url()
        onboard_cmd = f"curl -s {public_url}/api/v1/onboard/claim?token={onboard_token} | bash"

        return onboard_token, onboard_cmd
