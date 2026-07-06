"""Service 层全面单元测试"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.agent_service import AgentService
from app.services.skill_service import SkillService
from app.services.knowledge_service import KnowledgeService
from app.services.compliance_service import ComplianceService
from app.services.audit_service import AuditService
from app.services.heartbeat_service import HeartbeatService
from app.services.security_service import SecurityService
from app.services.onboard_service import OnboardService
from app.schemas.agent import AgentCreate
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate
from app.schemas.heartbeat import HeartbeatRequest, AgentInfo, InstalledSkill, ToolInfo
from app.schemas.skill import SkillCreate
from app.models.agent import Agent
from app.models.skill import Skill
from app.models.knowledge_entry import KnowledgeEntry
from app.models.audit_log import AuditLog
from app.models.agent_skill import AgentSkill
from app.models.security_scan import SecurityScan
from app.models.system_config import SystemConfig


class TestAgentService:
    """Agent 管理服务测试"""

    async def test_create_agent(self, db_session):
        service = AgentService(db_session)
        data = AgentCreate(agent_name="test-agent", agent_type="generic")
        agent, app_secret, onboard_token, onboard_cmd = await service.create_agent(data)

        assert agent.agent_name == "test-agent"
        assert agent.agent_type == "generic"
        assert agent.app_id.startswith("qw_")
        assert len(app_secret) > 20
        assert len(onboard_token) > 10
        assert "onboard" in onboard_cmd
        assert agent.status == "offline"

    async def test_get_agent_by_app_id(self, db_session):
        service = AgentService(db_session)
        data = AgentCreate(agent_name="get-test")
        agent, _, _, _ = await service.create_agent(data)

        found = await service.get_agent_by_app_id(agent.app_id)
        assert found is not None
        assert found.id == agent.id

        not_found = await service.get_agent_by_app_id("non_existent")
        assert not_found is None

    async def test_list_agents_empty(self, db_session):
        service = AgentService(db_session)
        agents = await service.list_agents()
        assert len(agents) == 0

    async def test_list_agents(self, db_session):
        service = AgentService(db_session)
        await service.create_agent(AgentCreate(agent_name="agent1"))
        await service.create_agent(AgentCreate(agent_name="agent2"))

        agents = await service.list_agents()
        assert len(agents) == 2

    async def test_delete_agent(self, db_session):
        service = AgentService(db_session)
        agent, _, _, _ = await service.create_agent(AgentCreate(agent_name="to-delete"))

        ok = await service.delete_agent(agent.id)
        assert ok is True

        # 软删除后 get_agent 返回 None（因为过滤了 is_deleted=0）
        not_found = await service.get_agent(agent.id)
        assert not_found is None

    async def test_delete_nonexistent(self, db_session):
        service = AgentService(db_session)
        ok = await service.delete_agent("nonexistent")
        assert ok is False

    async def test_update_heartbeat(self, db_session):
        service = AgentService(db_session)
        agent, _, _, _ = await service.create_agent(AgentCreate(agent_name="hb-test"))

        await service.update_heartbeat(agent, "192.168.1.100", "1.0.0")
        assert agent.status == "online"
        assert agent.host_ip == "192.168.1.100"
        assert agent.version == "1.0.0"

    async def test_get_agent_installed_skills_empty(self, db_session):
        service = AgentService(db_session)
        agent, _, _, _ = await service.create_agent(AgentCreate(agent_name="empty-skills"))

        skills = await service.get_agent_installed_skills(agent.id)
        assert skills == []


class TestSkillService:
    """技能管理服务测试"""

    async def test_create_skill(self, db_session):
        service = SkillService(db_session)
        data = SkillCreate(skill_name="pdf-tool", display_name="PDF Tool",
                           description="Handle PDF files", category="document")
        skill = await service.create_skill(data)

        assert skill.skill_name == "pdf-tool"
        assert skill.display_name == "PDF Tool"
        assert skill.version == "1.0.0"
        assert skill.scope == "public"
        assert skill.security_status == "pending"

    async def test_list_skills_empty(self, db_session):
        service = SkillService(db_session)
        skills = await service.list_skills()
        assert len(skills) == 0

    async def test_list_skills_with_data(self, db_session):
        service = SkillService(db_session)
        await service.create_skill(SkillCreate(skill_name="skill1"))
        await service.create_skill(SkillCreate(skill_name="skill2"))

        skills = await service.list_skills()
        assert len(skills) == 2

    async def test_get_skill(self, db_session):
        service = SkillService(db_session)
        created = await service.create_skill(SkillCreate(skill_name="find-me"))

        found = await service.get_skill("find-me")
        assert found is not None
        assert found.id == created.id

        not_found = await service.get_skill("not-exist")
        assert not_found is None

    async def test_assign_and_unassign_skill(self, db_session):
        # 先创建 Agent 和 Skill
        agent_svc = AgentService(db_session)
        agent, _, _, _ = await agent_svc.create_agent(AgentCreate(agent_name="assign-test"))

        skill_svc = SkillService(db_session)
        skill = await skill_svc.create_skill(SkillCreate(skill_name="assignable"))

        # 分配
        await skill_svc.assign_skill(skill.id, [agent.id])

        # 验证 AgentSkill 存在
        from sqlalchemy import select
        result = await db_session.execute(
            select(AgentSkill).where(AgentSkill.agent_id == agent.id, AgentSkill.skill_id == skill.id)
        )
        ag_sk = result.scalar_one_or_none()
        assert ag_sk is not None
        assert ag_sk.status == "pending"

        # 取消分配
        await skill_svc.unassign_skill(skill.id, [agent.id])
        result = await db_session.execute(
            select(AgentSkill).where(AgentSkill.agent_id == agent.id, AgentSkill.skill_id == skill.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_block_skill(self, db_session):
        service = SkillService(db_session)
        skill = await service.create_skill(SkillCreate(skill_name="to-block"))

        await service.block_skill(skill.id)

        await db_session.refresh(skill)
        assert skill.is_blocked == 1

    async def test_update_scope(self, db_session):
        service = SkillService(db_session)
        skill = await service.create_skill(SkillCreate(skill_name="scope-test"))

        await service.update_scope(skill.id, "public", True)
        await db_session.refresh(skill)
        assert skill.scope == "public"
        assert skill.is_mandatory == 1


class TestKnowledgeService:
    """知识库服务测试"""

    async def test_create_and_get(self, db_session):
        service = KnowledgeService(db_session)
        data = KnowledgeCreate(title="入职指南", content="# 入职指南\n欢迎加入！", category="onboarding")
        entry = await service.create(data)

        assert entry.title == "入职指南"
        assert entry.category == "onboarding"

        # get
        retrieved = await service.get(entry.id)
        assert retrieved is not None
        assert retrieved.content == "# 入职指南\n欢迎加入！"

    async def test_search(self, db_session):
        service = KnowledgeService(db_session)
        await service.create(KnowledgeCreate(title="API 文档", content="RESTful API 设计规范", category="dev"))
        await service.create(KnowledgeCreate(title="部署指南", content="Docker 部署步骤", category="ops"))

        results = await service.search("API")
        assert results.total == 1
        assert results.results[0].title == "API 文档"

        results = await service.search("部署")
        assert results.total == 1

        results = await service.search("不存在的关键字")
        assert results.total == 0

    async def test_update(self, db_session):
        service = KnowledgeService(db_session)
        entry = await service.create(KnowledgeCreate(title="旧标题", content="旧内容"))

        updated = await service.update(entry.id, KnowledgeUpdate(title="新标题"))
        assert updated is not None
        assert updated.title == "新标题"

    async def test_delete(self, db_session):
        service = KnowledgeService(db_session)
        entry = await service.create(KnowledgeCreate(title="待删除", content="内容"))

        ok = await service.delete(entry.id)
        assert ok is True

        retrieved = await service.get(entry.id)
        assert retrieved is None

    async def test_list_all(self, db_session):
        service = KnowledgeService(db_session)
        await service.create(KnowledgeCreate(title="A", content="a", category="cat1"))
        await service.create(KnowledgeCreate(title="B", content="b", category="cat2"))

        all_entries = await service.list_all()
        assert len(all_entries) == 2

        cat1_entries = await service.list_all("cat1")
        assert len(cat1_entries) == 1


class TestComplianceService:
    """合规检查服务测试"""

    async def test_check_compliance_no_mandatory(self, db_session):
        service = ComplianceService(db_session)
        agent_svc = AgentService(db_session)
        agent, _, _, _ = await agent_svc.create_agent(AgentCreate(agent_name="comp-test"))

        result = await service.check_compliance(agent.id)
        assert result.status == "compliant"
        assert result.missing_mandatory == []

    async def test_check_compliance_with_mandatory(self, db_session):
        compliance_svc = ComplianceService(db_session)
        agent_svc = AgentService(db_session)
        skill_svc = SkillService(db_session)

        agent, _, _, _ = await agent_svc.create_agent(AgentCreate(agent_name="comp-test2"))
        skill = await skill_svc.create_skill(SkillCreate(skill_name="must-have"))
        skill.is_mandatory = 1
        await db_session.commit()

        result = await compliance_svc.check_compliance(agent.id)
        assert result.status == "non_compliant"
        assert "must-have" in result.missing_mandatory

    async def test_get_global_compliance(self, db_session):
        service = ComplianceService(db_session)
        agent_svc = AgentService(db_session)
        await agent_svc.create_agent(AgentCreate(agent_name="comp-agent1"))
        await agent_svc.create_agent(AgentCreate(agent_name="comp-agent2"))

        results = await service.get_global_compliance()
        assert len(results) == 2


class TestAuditService:
    """审计日志服务测试"""

    async def test_log(self, db_session):
        service = AuditService(db_session)
        entry = await service.log("agent.create", "admin", "test-agent", "details here", "127.0.0.1")

        assert entry.action == "agent.create"
        assert entry.actor == "admin"
        assert entry.target == "test-agent"
        assert entry.details == "details here"
        assert entry.ip_address == "127.0.0.1"

    async def test_list_logs(self, db_session):
        service = AuditService(db_session)
        await service.log("action1", "admin", "target1")
        await service.log("action2", "user", "target2")

        logs, total = await service.list_logs()
        assert len(logs) == 2
        assert total >= 2

        filtered, _ = await service.list_logs(action="action1")
        assert len(filtered) == 1
        assert filtered[0].action == "action1"

    async def test_get_stats(self, db_session):
        service = AuditService(db_session)
        await service.log("agent.create", "admin", "a1")
        await service.log("skill.upload", "admin", "s1")

        stats = await service.get_stats()
        assert stats["total_logs"] >= 2
        assert "agent.create" in stats["action_distribution"]
        assert "skill.upload" in stats["action_distribution"]


class TestSecurityService:
    """安全检测服务测试"""

    async def test_run_static_analysis_safe(self, db_session):
        from app.models.skill import Skill
        skill = Skill(id=str(uuid.uuid4()), skill_name="safe-skill")
        db_session.add(skill)
        await db_session.commit()

        service = SecurityService(db_session)
        scan = await service.run_static_analysis(skill.id, "# Safe content\nprint('hello')")

        assert scan.status == "completed"
        assert scan.risk_level == "none"
        assert scan.findings == "[]"

    async def test_run_static_analysis_dangerous(self, db_session):
        from app.models.skill import Skill
        skill = Skill(id=str(uuid.uuid4()), skill_name="danger-skill")
        db_session.add(skill)
        await db_session.commit()

        content = '''
import os
os.system("nmap -sT 192.168.1.0/24")
import requests
requests.get("http://evil.com")
eval("malicious code")
'''
        service = SecurityService(db_session)
        scan = await service.run_static_analysis(skill.id, content)

        assert scan.status == "completed"
        import json
        findings = json.loads(scan.findings)
        assert len(findings) >= 3  # shell_exec, network_outbound, code_obfuscation
        # 最高风险应该是 high
        assert scan.risk_level == "high"

        # 验证技能状态已更新
        await db_session.refresh(skill)
        assert skill.security_status == "warning"
        assert skill.security_risk_level == "high"


class TestHeartbeatService:
    """心跳服务测试"""

    async def test_process_heartbeat_unknown_agent(self, db_session):
        service = HeartbeatService(db_session)
        data = HeartbeatRequest(
            agent_info=AgentInfo(name="unknown", type="generic"),
        )
        resp = await service.process_heartbeat("unknown_app_id", data)
        assert resp.status == "error"

    async def test_process_heartbeat_normal(self, db_session):
        # 先创建 Agent
        agent_svc = AgentService(db_session)
        agent, app_secret, _, _ = await agent_svc.create_agent(AgentCreate(agent_name="hb-test2"))

        service = HeartbeatService(db_session)
        data = HeartbeatRequest(
            agent_info=AgentInfo(name="hb-test2", type="generic", version="1.0", host_ip="10.0.0.1"),
            installed_skills=[],
            available_tools=[ToolInfo(name="nmap", version="7.95", path="/usr/bin/nmap")],
        )
        resp = await service.process_heartbeat(agent.app_id, data)

        assert resp.status == "ok"
        assert resp.last_heartbeat_at != ""

        # 验证状态更新
        await db_session.refresh(agent)
        assert agent.status == "online"
        assert agent.host_ip == "10.0.0.1"
        assert agent.version == "1.0"


class TestOnboardService:
    """一键接入服务测试"""

    async def test_generate_script_with_invalid_token(self, db_session):
        service = OnboardService(db_session)
        script = await service.generate_script("invalid_token", "http://localhost:8200")
        assert script is None

    async def test_claim_token_with_invalid_token(self, db_session):
        service = OnboardService(db_session)
        result = await service.claim_token("invalid_token")
        assert result is None
