"""数据库模型测试 — 验证模型基础结构"""

from app.models.agent import Agent
from app.models.skill import Skill
from app.models.agent_skill import AgentSkill
from app.models.security_scan import SecurityScan
from app.models.knowledge_entry import KnowledgeEntry
from app.models.audit_log import AuditLog
from app.models.compliance_check import ComplianceCheck
from app.models.tool import Tool
from app.models.system_config import SystemConfig


class TestModels:
    """验证模型类可正确实例化，并包含必要属性"""

    def test_agent_fields(self):
        agent = Agent(agent_name="test", app_id="qw_test", app_secret_hash="hash")
        assert agent.agent_name == "test"
        assert agent.app_id == "qw_test"

    def test_skill_fields(self):
        skill = Skill(skill_name="test-skill")
        assert skill.skill_name == "test-skill"
        assert skill.__tablename__ == "skill"

    def test_agent_skill_fields(self):
        as_ = AgentSkill(agent_id="a1", skill_id="s1")
        assert as_.agent_id == "a1"
        assert as_.skill_id == "s1"

    def test_knowledge_entry_fields(self):
        entry = KnowledgeEntry(title="Test", content="# Hello")
        assert entry.title == "Test"
        assert entry.content == "# Hello"

    def test_security_scan_fields(self):
        scan = SecurityScan(skill_id="s1", scan_type="static")
        assert scan.skill_id == "s1"
        assert scan.scan_type == "static"

    def test_audit_log_fields(self):
        log = AuditLog(action="test.action", actor="admin")
        assert log.action == "test.action"
        assert log.actor == "admin"

    def test_compliance_check_fields(self):
        cc = ComplianceCheck(agent_id="a1", status="compliant")
        assert cc.agent_id == "a1"
        assert cc.status == "compliant"

    def test_tool_fields(self):
        tool = Tool(agent_id="a1", tool_name="nmap")
        assert tool.agent_id == "a1"
        assert tool.tool_name == "nmap"

    def test_system_config_fields(self):
        sc = SystemConfig(config_key="test_key", config_value="test_val")
        assert sc.config_key == "test_key"
        assert sc.config_value == "test_val"

    def test_all_models_have_tablename(self):
        """所有模型类都有正确的表名"""
        assert Agent.__tablename__ == "agent"
        assert Skill.__tablename__ == "skill"
        assert AgentSkill.__tablename__ == "agent_skill"
        assert KnowledgeEntry.__tablename__ == "knowledge_entry"
        assert SecurityScan.__tablename__ == "security_scan"
        assert AuditLog.__tablename__ == "audit_log"
        assert ComplianceCheck.__tablename__ == "compliance_check"
        assert Tool.__tablename__ == "tool"
        assert SystemConfig.__tablename__ == "system_config"
