"""公共平台对接服务 — ClawHub / SkillHub 搜索与导入"""

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillScope, SecurityStatus, RiskLevel, SkillSource
from app.services.security_service import SecurityService
from app.services.sandbox_service import SandboxService
from app.config import settings


class PublicHubService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str, source: str | None = None) -> list[dict]:
        """搜索公共平台"""
        results = []

        if source is None or source == "clawhub":
            try:
                clawhub_results = await self._search_clawhub(query)
                results.extend(clawhub_results)
            except Exception as e:
                pass

        if source is None or source == "skillhub":
            try:
                skillhub_results = await self._search_skillhub(query)
                results.extend(skillhub_results)
            except Exception as e:
                pass

        # 去重：同名技能优先展示
        seen = set()
        deduped = []
        for r in results:
            key = f"{r['name']}|{r['source']}"
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped

    async def _search_clawhub(self, query: str) -> list[dict]:
        """搜索 ClawHub"""
        try:
            result = subprocess.run(
                ["clawhub", "search", query, "--format", "json"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                skills = data if isinstance(data, list) else data.get("skills", [])
                return [{
                    "name": s.get("name", ""),
                    "display_name": s.get("display_name", s.get("name", "")),
                    "description": s.get("description", ""),
                    "version": s.get("latest_version", s.get("version", "1.0.0")),
                    "category": s.get("category", "uncategorized"),
                    "source": "clawhub",
                    "source_url": s.get("url", f"https://clawhub.com/skills/{s.get('name', '')}"),
                    "download_count": s.get("download_count", 0),
                } for s in skills]
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass
        return []

    async def _search_skillhub(self, query: str) -> list[dict]:
        """搜索 SkillHub"""
        try:
            result = subprocess.run(
                ["skillhub", "search", query, "--format", "json"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                skills = data if isinstance(data, list) else data.get("skills", [])
                return [{
                    "name": s.get("name", ""),
                    "display_name": s.get("display_name", s.get("name", "")),
                    "description": s.get("description", ""),
                    "version": s.get("latest_version", s.get("version", "1.0.0")),
                    "category": s.get("category", "uncategorized"),
                    "source": "skillhub",
                    "source_url": s.get("url", ""),
                    "download_count": s.get("download_count", 0),
                } for s in skills]
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass
        return []

    async def import_skill(self, name: str, source: str, source_url: str | None = None) -> dict:
        """从公共平台导入技能 → 自动安检"""
        # 下载技能
        skill_data = await self._download_from_platform(name, source)
        if not skill_data:
            raise ValueError(f"无法从 {source} 下载技能 {name}")

        content = skill_data.get("content", "")
        version = skill_data.get("version", "1.0.0")
        description = skill_data.get("description", "")

        # 创建技能记录
        skill = Skill(
            id=str(uuid.uuid4()),
            skill_name=name,
            display_name=skill_data.get("display_name", name),
            description=description,
            category=skill_data.get("category", "uncategorized"),
            version=version,
            scope=SkillScope.PRIVATE.value,
            source=source,
            source_url=source_url or "",
            security_status=SecurityStatus.SCANNING.value,
        )
        self.db.add(skill)
        await self.db.commit()

        # 保存文件
        skill_dir = Path(settings.skills_dir) / name / version
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

        # Tier 1 静态分析
        security_service = SecurityService(self.db)
        scan1 = await security_service.run_static_analysis(skill.id, content)

        # Tier 2 沙箱检测
        try:
            sandbox_service = SandboxService(self.db)
            scan2 = await sandbox_service.run_sandbox_scan(skill.id, name, content)
        except Exception:
            pass

        await self.db.refresh(skill)

        return {
            "id": skill.id,
            "name": skill.skill_name,
            "version": skill.version,
            "security_status": skill.security_status,
            "security_risk_level": skill.security_risk_level,
            "source": source,
        }

    async def _download_from_platform(self, name: str, source: str) -> dict | None:
        """从平台下载技能"""
        if source == "clawhub":
            return await self._download_clawhub(name)
        elif source == "skillhub":
            return await self._download_skillhub(name)
        return None

    async def _download_clawhub(self, name: str) -> dict | None:
        try:
            result = subprocess.run(
                ["clawhub", "download", name, "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "content": data.get("content", ""),
                    "version": data.get("version", "1.0.0"),
                    "display_name": data.get("display_name", name),
                    "description": data.get("description", ""),
                    "category": data.get("category", "uncategorized"),
                }
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        return None

    async def _download_skillhub(self, name: str) -> dict | None:
        try:
            result = subprocess.run(
                ["skillhub", "download", name, "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "content": data.get("content", ""),
                    "version": data.get("version", "1.0.0"),
                    "display_name": data.get("display_name", name),
                    "description": data.get("description", ""),
                    "category": data.get("category", "uncategorized"),
                }
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        return None
