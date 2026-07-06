"""技能管理服务"""

import uuid
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillScope, SecurityStatus, RiskLevel, SkillSource
from app.models.agent_skill import AgentSkill, AgentSkillStatus
from app.models.agent import Agent
from app.schemas.skill import (
    SkillListItem, SkillGetResponse, SkillDownloadResponse,
    SkillFileItem, SkillCreate,
)
from app.config import settings


class SkillService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_skills(
        self, category: str | None = None, scope: str | None = None,
        agent_id: str | None = None, include_blocked: bool = False,
    ) -> list[SkillListItem]:
        """获取技能列表（Agent 可见的：公开 + 分配给自己的私有）"""
        conditions = [Skill.is_deleted == 0, Skill.is_active == 1]
        if not include_blocked:
            conditions.append(Skill.is_blocked == 0)
        if category:
            conditions.append(Skill.category == category)

        # Agent 可见的 skill: scope=public OR 分配给了该 Agent
        if agent_id:
            subq = select(AgentSkill.skill_id).where(AgentSkill.agent_id == agent_id)
            conditions.append(or_(Skill.scope == SkillScope.PUBLIC.value, Skill.id.in_(subq)))
        else:
            # 管理视角：全部
            if scope:
                conditions.append(Skill.scope == scope)

        stmt = select(Skill).where(*conditions).order_by(Skill.created_at.desc())
        result = await self.db.execute(stmt)
        skills = []
        for sk in result.scalars():
            skills.append(SkillListItem(
                name=sk.skill_name,
                version=sk.version,
                display_name=sk.display_name,
                description=sk.description,
                category=sk.category,
                scope=sk.scope,
                security_status=sk.security_status,
                security_risk_level=sk.security_risk_level,
                is_mandatory=bool(sk.is_mandatory),
                size_bytes=0,
            ))
        return skills

    async def get_skill(self, name: str) -> Skill | None:
        result = await self.db.execute(
            select(Skill).where(Skill.skill_name == name, Skill.is_deleted == 0)
        )
        return result.scalar_one_or_none()

    async def get_skill_detail(self, name: str, agent_id: str | None = None) -> SkillGetResponse | None:
        """获取技能详情（含文件列表）"""
        skill = await self.get_skill(name)
        if not skill:
            return None

        # 检查可见性
        if skill.scope == SkillScope.PRIVATE.value and agent_id:
            ag_sk = await self._get_agent_skill(agent_id, skill.id)
            if not ag_sk:
                return None

        # 扫描实际文件
        files = []
        skill_dir = Path(settings.skills_dir) / skill.skill_name / skill.version
        if skill_dir.exists():
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    files.append({"path": str(f.relative_to(skill_dir)), "size_bytes": f.stat().st_size})

        return SkillGetResponse(
            name=skill.skill_name,
            version=skill.version,
            display_name=skill.display_name,
            description=skill.description,
            category=skill.category,
            scope=skill.scope,
            security_status=skill.security_status,
            security_risk_level=skill.security_risk_level,
            is_mandatory=bool(skill.is_mandatory),
            files=files,
            source=skill.source,
            source_url=skill.source_url,
        )

    async def create_skill(self, data: SkillCreate) -> Skill:
        """创建技能记录"""
        skill = Skill(
            id=str(uuid.uuid4()),
            skill_name=data.skill_name,
            display_name=data.display_name or data.skill_name,
            description=data.description,
            category=data.category,
            version=data.version,
            scope=data.scope or SkillScope.PRIVATE.value,
            source="local",
        )
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def download_skill(self, name: str, agent_id: str | None = None) -> SkillDownloadResponse | None:
        """下载技能包"""
        skill = await self.get_skill(name)
        if not skill or skill.is_blocked:
            return None

        if skill.scope == SkillScope.PRIVATE.value and agent_id:
            ag_sk = await self._get_agent_skill(agent_id, skill.id)
            if not ag_sk:
                return None

        # 读取实际文件
        files = []
        skill_dir = Path(settings.skills_dir) / skill.skill_name / skill.version
        if skill_dir.exists() and skill_dir.is_dir():
            for f in sorted(skill_dir.rglob("*")):
                if f.is_file():
                    rel_path = str(f.relative_to(skill_dir))
                    content = f.read_bytes()
                    is_text = self._is_text_file(rel_path)
                    files.append(SkillFileItem(
                        path=rel_path,
                        content=content.decode() if is_text else content.hex(),
                        encoding="utf-8" if is_text else "hex",
                        size_bytes=len(content),
                        sha256=hashlib.sha256(content).hexdigest(),
                    ))

        # 更新 AgentSkill 状态
        if agent_id:
            ag_sk = await self._get_agent_skill(agent_id, skill.id)
            if ag_sk and ag_sk.status == AgentSkillStatus.PENDING:
                ag_sk.status = AgentSkillStatus.INSTALLED
                ag_sk.installed_version = skill.version
                ag_sk.installed_at = datetime.now(timezone.utc)
                await self.db.commit()

        return SkillDownloadResponse(
            skill=SkillListItem(
                name=skill.skill_name,
                version=skill.version,
                display_name=skill.display_name,
                description=skill.description,
                category=skill.category,
                scope=skill.scope,
                security_status=skill.security_status,
                security_risk_level=skill.security_risk_level,
                is_mandatory=bool(skill.is_mandatory),
                size_bytes=0,
            ),
            files=files,
        )

    async def assign_skill(self, skill_id: str, agent_ids: list[str]):
        """分配技能给 Agent"""
        for agent_id in agent_ids:
            existing = await self._get_agent_skill(agent_id, skill_id)
            if not existing:
                ag_sk = AgentSkill(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    skill_id=skill_id,
                    status=AgentSkillStatus.PENDING,
                )
                self.db.add(ag_sk)
        await self.db.commit()

    async def unassign_skill(self, skill_id: str, agent_ids: list[str]):
        for agent_id in agent_ids:
            ag_sk = await self._get_agent_skill(agent_id, skill_id)
            if ag_sk:
                await self.db.delete(ag_sk)
        await self.db.commit()

    async def update_scope(self, skill_id: str, scope: str, is_mandatory: bool | None = None):
        skill = await self.db.get(Skill, skill_id)
        if skill:
            skill.scope = scope
            if is_mandatory is not None:
                skill.is_mandatory = 1 if is_mandatory else 0
            await self.db.commit()

    async def block_skill(self, skill_id: str):
        skill = await self.db.get(Skill, skill_id)
        if skill:
            skill.is_blocked = 1
            await self.db.commit()

    async def save_skill_files(self, skill_name: str, version: str, files: list[SkillFileItem]):
        """保存技能文件到磁盘"""
        skill_dir = Path(settings.skills_dir) / skill_name / version
        skill_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            file_path = skill_dir / f.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if f.encoding == "base64":
                import base64
                file_path.write_bytes(base64.b64decode(f.content))
            elif f.encoding == "hex":
                file_path.write_bytes(bytes.fromhex(f.content))
            else:
                file_path.write_text(f.content, encoding="utf-8")

    async def _get_agent_skill(self, agent_id: str, skill_id: str) -> AgentSkill | None:
        result = await self.db.execute(
            select(AgentSkill).where(
                AgentSkill.agent_id == agent_id,
                AgentSkill.skill_id == skill_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _is_text_file(path: str) -> bool:
        ext = Path(path).suffix.lower()
        return ext in {".md", ".txt", ".json", ".yaml", ".yml", ".toml",
                       ".py", ".js", ".ts", ".sh", ".bat", ".conf",
                       ".cfg", ".ini", ".env", ".xml", ".html", ".css"}
