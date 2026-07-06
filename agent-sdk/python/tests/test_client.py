"""Agent Hub Python SDK 测试"""

from agent_hub import AgentHubClient, MCPAgentClient, AgentInfo, InstalledSkill, ToolInfo


class TestClient:
    """REST 客户端测试"""

    def test_constructor(self):
        client = AgentHubClient("http://localhost:8200", "qw_test", "secret123")
        assert client.base_url == "http://localhost:8200"
        assert client.app_id == "qw_test"
        assert client.app_secret == "secret123"
        assert client.max_retries == 3

    def test_generate_mcp_signature(self):
        ts, nonce, sig = AgentHubClient.generate_mcp_signature("qw_test", "secret")
        assert len(ts) > 0
        assert len(nonce) > 0
        assert len(sig) == 64  # SHA256 hex

    def test_agent_info_defaults(self):
        info = AgentInfo(name="test-agent")
        assert info.name == "test-agent"
        assert info.type == "generic"
        assert info.mcp_supported is True

    def test_installed_skill_defaults(self):
        skill = InstalledSkill(name="pdf", version="1.0.0")
        assert skill.status == "active"

    def test_tool_info_defaults(self):
        tool = ToolInfo(name="nmap")
        assert tool.version is None


class TestMCPClient:
    """MCP 客户端测试"""

    def test_constructor(self):
        client = MCPAgentClient("http://localhost:8200", "qw_test", "secret")
        assert "localhost:8200" in client.server_url
        assert client.app_id == "qw_test"
        assert client._connected is False
        assert client._session_id is None
