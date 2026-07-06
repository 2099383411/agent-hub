"""Tier 2 沙箱引擎测试"""

import pytest
from app.services.sandbox_service import SandboxService


class TestSandboxService:
    """沙箱执行引擎单元测试"""

    def _make_service(self):
        return SandboxService.__new__(SandboxService)

    def test_extract_scripts_python(self):
        content = '```python\nprint("hello world")\n```'
        service = self._make_service()
        scripts = service._extract_scripts(content)
        assert len(scripts) == 1
        assert scripts[0][1] == 'print("hello world")'

    def test_extract_scripts_shell(self):
        content = '```bash\necho "hello"\n```\n```sh\nls -la\n```'
        service = self._make_service()
        scripts = service._extract_scripts(content)
        assert len(scripts) == 2

    def test_extract_scripts_empty(self):
        content = '# No code blocks here'
        service = self._make_service()
        scripts = service._extract_scripts(content)
        assert len(scripts) == 0

    def test_calculate_max_risk(self):
        service = self._make_service()
        assert service._calculate_max_risk([{"risk": "low"}, {"risk": "medium"}]) == "medium"
        assert service._calculate_max_risk([{"risk": "high"}, {"risk": "medium"}]) == "high"
        assert service._calculate_max_risk([]) == "none"

    async def test_network_access_safe(self):
        service = self._make_service()
        findings = await service._check_network_access("# http://localhost:8080")
        assert len(findings) == 0

    async def test_network_access_dangerous(self):
        service = self._make_service()
        findings = await service._check_network_access("https://evil.com/payload")
        assert len(findings) >= 1

    async def test_filesystem_ops_safe(self):
        service = self._make_service()
        findings = await service._check_filesystem_ops('with open("local.txt", "r"): pass')
        assert len(findings) == 0

    async def test_filesystem_ops_dangerous(self):
        service = self._make_service()
        findings = await service._check_filesystem_ops("cat /etc/passwd")
        assert len(findings) >= 1
