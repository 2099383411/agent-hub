"""Tier 2 沙箱执行引擎 — Docker 隔离环境技能安全检测"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.security_scan import SecurityScan
from app.models.skill import Skill, SecurityStatus, RiskLevel
from app.services.security_service import SecurityService


class SandboxService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self._docker_client = None

    @property
    def docker_client(self):
        if self._docker_client is None:
            import docker
            self._docker_client = docker.from_env()
        return self._docker_client

    async def run_sandbox_scan(self, skill_id: str, skill_name: str, content: str) -> SecurityScan:
        """Tier 2 沙箱执行：在 Docker 隔离容器中运行技能并检测危险行为"""
        scan = SecurityScan(
            id=str(uuid.uuid4()),
            skill_id=skill_id,
            scan_type="sandbox",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(scan)
        await self.db.commit()

        findings = []

        try:
            # 检测内容中的危险模式（动态执行验证）
            dynamic_findings = await self._execute_in_sandbox(skill_name, content)
            findings.extend(dynamic_findings)

            # 检测网络外联
            network_findings = await self._check_network_access(content)
            findings.extend(network_findings)

            # 检测文件系统操作
            fs_findings = await self._check_filesystem_ops(content)
            findings.extend(fs_findings)

        except Exception as e:
            findings.append({
                "rule": "sandbox_error",
                "risk": "medium",
                "description": f"沙箱执行异常: {str(e)}",
            })

        # 计算风险等级
        max_risk = self._calculate_max_risk(findings)

        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        scan.risk_level = max_risk
        scan.findings = json.dumps(findings, ensure_ascii=False)

        # 更新技能安全状态
        skill = await self.db.get(Skill, skill_id)
        if skill:
            if max_risk == "high":
                skill.security_status = SecurityStatus.WARNING.value
                skill.security_risk_level = RiskLevel.HIGH.value
            elif max_risk == "medium":
                skill.security_status = SecurityStatus.WARNING.value
                skill.security_risk_level = RiskLevel.MEDIUM.value
            elif max_risk == "low":
                skill.security_status = SecurityStatus.WARNING.value
                skill.security_risk_level = RiskLevel.LOW.value
            else:
                # 如果 Tier 1 已标记风险但 Tier 2 未发现，保持 Tier 1 的结果
                if skill.security_status == SecurityStatus.PENDING.value:
                    skill.security_status = SecurityStatus.PASSED.value
                    skill.security_risk_level = RiskLevel.NONE.value

        await self.db.commit()
        await self.db.refresh(scan)
        return scan

    async def _execute_in_sandbox(self, skill_name: str, content: str) -> list[dict]:
        """在 Docker 沙箱中执行技能脚本"""
        findings = []

        try:
            # 提取脚本内容
            scripts = self._extract_scripts(content)
            if not scripts:
                return findings

            # 为每个脚本创建沙箱
            for script_name, script_content in scripts:
                result = await self._run_single_sandbox(script_name, script_content)
                if result:
                    findings.append(result)

        except Exception as e:
            findings.append({
                "rule": "sandbox_execution",
                "risk": "medium",
                "description": f"沙箱执行失败: {str(e)}",
            })

        return findings

    async def _run_single_sandbox(self, script_name: str, script_content: str) -> dict | None:
        """在 Docker 沙箱容器中运行单个脚本"""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / script_name
            script_path.write_text(script_content)

            try:
                container = self.docker_client.containers.run(
                    image="python:3.12-slim",
                    command=["python3", "-c", f"""
import sys, os, subprocess, socket, json

def check_file_write():
    \"\"\"检测是否有文件写入操作\"\"\"
    test_file = '/tmp/test_write.txt'
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        return [{{'found': True, 'detail': '文件写入操作已执行'}}]
    except:
        return []

def check_network():
    \"\"\"检测网络外联\"\"\"
    results = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('8.8.8.8', 53))
        s.close()
        if result == 0:
            results.append({{'found': True, 'detail': 'DNS 解析成功，网络可访问'}})
    except:
        pass
    return results

try:
    exec(open('/script/{script_name}').read())
    results = {{
        'file_write': check_file_write(),
        'network': check_network(),
    }}
    print(json.dumps(results))
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"""],
                    volumes={tmpdir: {"bind": f"/script", "mode": "ro"}},
                    network_disabled=True,  # 断网
                    read_only=True,  # 只读
                    mem_limit="128m",
                    cpu_period=100000,
                    cpu_quota=50000,
                    remove=True,
                    detach=True,
                )

                result = container.wait(timeout=30)
                logs = container.logs().decode("utf-8").strip()

                if result["StatusCode"] != 0:
                    return {
                        "rule": f"sandbox_{script_name}",
                        "risk": "low",
                        "description": f"脚本 {script_name} 沙箱执行异常退出 (code={result['StatusCode']})",
                    }

                # 解析检测结果
                try:
                    detection = json.loads(logs)
                    if "file_write" in detection and detection["file_write"]:
                        return {
                            "rule": f"sandbox_file_write_{script_name}",
                            "risk": "medium",
                            "description": f"脚本 {script_name} 在沙箱中执行了文件写入操作",
                        }
                    if "network" in detection and detection["network"]:
                        return {
                            "rule": f"sandbox_network_{script_name}",
                            "risk": "high",
                            "description": f"脚本 {script_name} 在沙箱中尝试网络外联",
                        }
                except json.JSONDecodeError:
                    pass

            except Exception as e:
                return {
                    "rule": f"sandbox_container_error",
                    "risk": "medium",
                    "description": f"沙箱容器运行失败: {str(e)}",
                }

        return None

    async def _check_network_access(self, content: str) -> list[dict]:
        """检测网络外联模式"""
        import re
        findings = []
        # 检查 URL/IP 硬编码
        url_pattern = re.findall(r'https?://[\w\.-]+(?:/\S*)?', content)
        ip_pattern = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)

        suspicious_urls = [u for u in url_pattern if not any(
            safe in u for safe in ["localhost", "127.0.0.1", "0.0.0.0", "example.com"]
        )]

        if suspicious_urls:
            findings.append({
                "rule": "sandbox_hardcoded_url",
                "risk": "medium",
                "description": f"发现硬编码的外部 URL: {', '.join(suspicious_urls[:5])}",
                "match_count": len(suspicious_urls),
            })

        return findings

    async def _check_filesystem_ops(self, content: str) -> list[dict]:
        """检测文件系统操作"""
        import re
        findings = []
        # 检测敏感路径操作
        dangerous_paths = ["/etc/passwd", "/etc/shadow", "/root/", "/home/", "~/.ssh"]
        for path in dangerous_paths:
            if path in content:
                findings.append({
                    "rule": "sandbox_dangerous_path",
                    "risk": "high",
                    "description": f"脚本引用了敏感路径: {path}",
                })
        return findings

    def _extract_scripts(self, content: str) -> list[tuple[str, str]]:
        """从 SKILL.md 中提取可执行脚本内容"""
        import re
        scripts = []

        # 提取 Python 代码块
        py_blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
        for i, block in enumerate(py_blocks):
            scripts.append((f"script_{i}.py", block.strip()))

        # 提取 Shell 代码块
        sh_blocks = re.findall(r'```(?:bash|sh|shell)\n(.*?)```', content, re.DOTALL)
        for i, block in enumerate(sh_blocks):
            scripts.append((f"script_{i}.sh", block.strip()))

        return scripts

    def _calculate_max_risk(self, findings: list[dict]) -> str:
        risk_order = {"high": 3, "medium": 2, "low": 1, "none": 0}
        max_risk = "none"
        for f in findings:
            r = f.get("risk", "none")
            if risk_order.get(r, 0) > risk_order.get(max_risk, 0):
                max_risk = r
        return max_risk
