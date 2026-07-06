"""MCP Server — FastMCP 实现"""

import json
from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.services.skill_service import SkillService
from app.services.heartbeat_service import HeartbeatService
from app.services.knowledge_service import KnowledgeService
from app.services.compliance_service import ComplianceService
from app.models.system_config import SystemConfig
from app.schemas.heartbeat import HeartbeatRequest
from sqlalchemy import select

mcp_app = FastMCP("agent-hub", port=8200)


def get_mcp_tools():
    """注册 MCP tools"""

    @mcp_app.tool()
    async def skills_list(category: str = None, scope: str = None) -> str:
        """获取技能列表（Agent 可见的技能）"""
        async with async_session() as db:
            service = SkillService(db)
            skills = await service.list_skills(category=category, scope=scope)
            return json.dumps({"skills": [s.model_dump() for s in skills], "total": len(skills)}, ensure_ascii=False)

    @mcp_app.tool()
    async def skills_get(name: str) -> str:
        """查看单个技能详情"""
        async with async_session() as db:
            service = SkillService(db)
            skill = await service.get_skill_detail(name)
            if not skill:
                return json.dumps({"error": "skill not found"}, ensure_ascii=False)
            return json.dumps(skill.model_dump(), ensure_ascii=False)

    @mcp_app.tool()
    async def skills_download(name: str) -> str:
        """下载技能包（含 SKILL.md 和所有附带文件）"""
        async with async_session() as db:
            service = SkillService(db)
            pkg = await service.download_skill(name)
            if not pkg:
                return json.dumps({"error": "skill not found or blocked"}, ensure_ascii=False)
            return json.dumps({
                "skill": pkg.skill.model_dump(),
                "files": [f.model_dump() for f in pkg.files],
            }, ensure_ascii=False)

    @mcp_app.tool()
    async def agent_heartbeat(data: str) -> str:
        """Agent 心跳上报"""
        try:
            req = HeartbeatRequest(**json.loads(data))
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

        async with async_session() as db:
            # 从上下文获取 app_id（实际通过 SSE 握手验证）
            service = HeartbeatService(db)
            resp = await service.process_heartbeat("", req)
            return json.dumps(resp.model_dump(), ensure_ascii=False)

    @mcp_app.tool()
    async def knowledge_search(query: str, category: str = None) -> str:
        """搜索知识库"""
        async with async_session() as db:
            service = KnowledgeService(db)
            resp = await service.search(query, category)
            return json.dumps(resp.model_dump(), ensure_ascii=False)

    @mcp_app.tool()
    async def knowledge_get(id: str) -> str:
        """获取知识条目全文"""
        async with async_session() as db:
            service = KnowledgeService(db)
            entry = await service.get(id)
            if not entry:
                return json.dumps({"error": "not found"}, ensure_ascii=False)
            return json.dumps(entry.model_dump(), ensure_ascii=False)

    @mcp_app.tool()
    async def hub_onboarding() -> str:
        """获取中台使用规范（入职手册）"""
        async with async_session() as db:
            result = await db.execute(
                select(SystemConfig).where(SystemConfig.config_key == "onboarding_content")
            )
            config = result.scalar_one_or_none()

            result = await db.execute(
                select(SystemConfig).where(SystemConfig.config_key == "onboarding_version")
            )
            ver_config = result.scalar_one_or_none()

            return json.dumps({
                "version": int(ver_config.config_value) if ver_config else 1,
                "content": config.config_value if config else "# Agent Hub\n\n请管理员在中台面板配置入职规范。",
                "updated_at": config.updated_at.isoformat() if config else "",
            }, ensure_ascii=False)

    @mcp_app.tool()
    async def agent_report_compliance(agent_id: str, compliance_data: str) -> str:
        """主动上报合规状态"""
        async with async_session() as db:
            try:
                data = json.loads(compliance_data)
            except Exception:
                return json.dumps({"status": "error", "message": "invalid JSON"}, ensure_ascii=False)
            return json.dumps({"status": "noted", "exemption_pending": True}, ensure_ascii=False)


def create_mcp_server():
    get_mcp_tools()
    return mcp_app
