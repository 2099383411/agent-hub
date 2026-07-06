from app.api.auth import router as auth_router
from app.api.agents import router as agents_router
from app.api.skills import router as skills_router
from app.api.security import router as security_router
from app.api.knowledge import router as knowledge_router
from app.api.compliance import router as compliance_router
from app.api.dashboard import router as dashboard_router
from app.api.onboard import router as onboard_router
from app.api.system import router as system_router
from app.api.public_hub import router as public_hub_router
from app.api.audit import router as audit_router
from app.api.agent_fallback import router as agent_fallback_router

__all__ = [
    "auth_router", "agents_router", "skills_router",
    "security_router", "knowledge_router", "compliance_router",
    "dashboard_router", "onboard_router", "system_router",
    "public_hub_router",
    "audit_router",
    "agent_fallback_router",
]
