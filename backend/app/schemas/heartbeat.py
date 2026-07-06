"""心跳相关 schema"""

from pydantic import BaseModel
from typing import Optional


class InstalledSkill(BaseModel):
    name: str
    version: str
    status: str = "active"


class ToolInfo(BaseModel):
    name: str
    version: str | None = None
    path: str | None = None


class AgentInfo(BaseModel):
    name: str
    type: str = "generic"
    version: str | None = None
    host_ip: str | None = None
    mcp_supported: bool = True


class HeartbeatRequest(BaseModel):
    agent_info: AgentInfo
    installed_skills: list[InstalledSkill] = []
    available_tools: list[ToolInfo] = []


class PendingSkill(BaseModel):
    name: str
    version: str
    mandatory: bool = False
    assigned_at: str | None = None
    scope: str = "private"


class OutdatedSkill(BaseModel):
    name: str
    current_version: str
    installed_version: str
    update_urgency: str = "recommended"


class ComplianceStatus(BaseModel):
    status: str = "compliant"
    missing_mandatory: list[str] = []
    total_mandatory: int = 0
    installed_mandatory: int = 0


class HeartbeatResponse(BaseModel):
    status: str = "ok"
    last_heartbeat_at: str = ""
    pending_skills: list[PendingSkill] = []
    outdated_skills: list[OutdatedSkill] = []
    compliance: ComplianceStatus
