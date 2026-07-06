"""Agent 相关 schema"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentCreate(BaseModel):
    agent_name: str
    agent_type: str = "generic"
    host_ip: str | None = None
    version: str | None = None


class AgentOut(BaseModel):
    id: str
    agent_name: str
    agent_type: str
    app_id: str
    status: str
    host_ip: str | None = None
    version: str | None = None
    last_heartbeat_at: datetime | None = None
    is_deleted: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentOnboardResponse(BaseModel):
    """创建 Agent 后的返回（含凭证）"""
    agent: AgentOut
    app_id: str
    app_secret: str
    onboard_command: str
    onboard_token: str


class AgentDetailOut(AgentOut):
    installed_skills: list[dict] = []
    compliance_status: str | None = None
    missing_mandatory: list[str] = []
