"""安全检测服务 — Tier 1 静态分析"""

import re
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.security_scan import SecurityScan
from app.models.skill import Skill, SecurityStatus, RiskLevel


# 危险模式检测规则
DANGEROUS_PATTERNS = [
    {"name": "shell_exec", "pattern": r'\b(exec|system|popen|subprocess\.call|os\.system|subprocess\.run)\s*\(', "risk": "high", "desc": "执行系统命令"},
    {"name": "network_outbound", "pattern": r'\b(requests\.(get|post)|urllib\.request|http\.(GET|POST)|curl|wget)\s*\(', "risk": "medium", "desc": "网络外联请求"},
    {"name": "file_write", "pattern": r'\b(open\s*\(.*["\'].*["\']\s*,\s*["\']w|write\s*\(|file_put_contents)', "risk": "medium", "desc": "文件写入操作"},
    {"name": "privilege_escalation", "pattern": r'\b(sudo|chmod\s+777|chown|setuid|setgid)\b', "risk": "high", "desc": "权限提升操作"},
    {"name": "code_obfuscation", "pattern": r'\b(eval|exec|compile|base64\.(b64decode|decode)|__import__)\s*\(', "risk": "medium", "desc": "代码混淆/动态执行"},
    {"name": "docker_escape", "pattern": r'/var/run/docker\.sock|--privileged|security_opt\s*=\s*\[\s*["\']privileged', "risk": "high", "desc": "Docker 逃逸风险"},
    {"name": "data_exfil", "pattern": r'\b(ftp|sftp|scp)\s+|nc\s+|ncat\s+', "risk": "high", "desc": "数据外传风险"},
    {"name": "env_leak", "pattern": r'\b(os\.(environ|getenv)|process\.env)\b', "risk": "low", "desc": "环境变量读取"},
]


class SecurityService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_static_analysis(self, skill_id: str, content: str) -> SecurityScan:
        """Tier 1 静态分析"""
        scan = SecurityScan(
            id=str(uuid.uuid4()),
            skill_id=skill_id,
            scan_type="static",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(scan)
        await self.db.commit()

        findings = []
        max_risk = "none"

        for rule in DANGEROUS_PATTERNS:
            matches = re.findall(rule["pattern"], content, re.IGNORECASE)
            if matches:
                risk_order = {"high": 3, "medium": 2, "low": 1, "none": 0}
                if risk_order.get(rule["risk"], 0) > risk_order.get(max_risk, 0):
                    max_risk = rule["risk"]

                findings.append({
                    "rule": rule["name"],
                    "risk": rule["risk"],
                    "description": rule["desc"],
                    "match_count": len(matches),
                    "sample": matches[0][:100] if matches else "",
                })

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
                skill.security_status = SecurityStatus.PASSED.value
                skill.security_risk_level = RiskLevel.NONE.value

        await self.db.commit()
        await self.db.refresh(scan)
        return scan

    async def get_scans(self, skill_id: str | None = None) -> list[SecurityScan]:
        stmt = select(SecurityScan).order_by(SecurityScan.created_at.desc())
        if skill_id:
            stmt = stmt.where(SecurityScan.skill_id == skill_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_scan(self, scan_id: str) -> SecurityScan | None:
        return await self.db.get(SecurityScan, scan_id)
