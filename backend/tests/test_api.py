"""API 集成测试 — 使用依赖覆盖 + 内存数据库"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def db_session():
    """替换 get_db 依赖的测试数据库会话"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """创建带依赖覆盖的测试客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Agent Hub"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/v1/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_auth_login(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={"password": settings.admin_password})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data

    # 错误密码
    resp = await client.post("/api/v1/auth/login", json={"password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_agent_crud(client: AsyncClient):
    """Agent CRUD"""
    # 登录
    auth_resp = await client.post("/api/v1/auth/login", json={"password": settings.admin_password})
    token = auth_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建
    resp = await client.post(
        "/api/v1/agents",
        json={"agent_name": "test-agent"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["agent"]["agent_name"] == "test-agent"
    agent_id = data["agent"]["id"]

    # 列表
    resp = await client.get("/api/v1/agents", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1

    # 详情
    resp = await client.get(f"/api/v1/agents/{agent_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["agent_name"] == "test-agent"

    # 删除
    resp = await client.delete(f"/api/v1/agents/{agent_id}", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_skill_upload(client: AsyncClient):
    """技能上传"""
    auth_resp = await client.post("/api/v1/auth/login", json={"password": settings.admin_password})
    token = auth_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    skill_content = "# Test Skill\n\n```python\nprint('hello')\n```"
    resp = await client.post(
        "/api/v1/skills/upload",
        data={"scope": "public", "is_mandatory": True},
        files={"file": ("test-skill.md", skill_content, "text/markdown")},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["skill_name"] == "test-skill"

    # 技能列表
    resp = await client.get("/api/v1/skills", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["skills"]) >= 1


@pytest.mark.asyncio
async def test_knowledge_crud(client: AsyncClient):
    """知识库 CRUD"""
    auth_resp = await client.post("/api/v1/auth/login", json={"password": settings.admin_password})
    token = auth_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建
    resp = await client.post(
        "/api/v1/knowledge",
        json={"title": "Doc", "content": "# Test", "category": "dev"},
        headers=headers,
    )
    assert resp.status_code == 200
    entry_id = resp.json()["data"]["id"]

    # 获取
    resp = await client.get(f"/api/v1/knowledge/{entry_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Doc"

    # 更新
    resp = await client.put(
        f"/api/v1/knowledge/{entry_id}",
        json={"title": "Updated"},
        headers=headers,
    )
    assert resp.status_code == 200

    # 删除
    resp = await client.delete(f"/api/v1/knowledge/{entry_id}", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_compliance_dashboard(client: AsyncClient):
    """合规 + 仪表盘"""
    auth_resp = await client.post("/api/v1/auth/login", json={"password": settings.admin_password})
    token = auth_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 合规
    resp = await client.get("/api/v1/compliance/status", headers=headers)
    assert resp.status_code == 200

    # 仪表盘
    resp = await client.get("/api/v1/dashboard/overview", headers=headers)
    assert resp.status_code == 200
    assert "agents" in resp.json()["data"]


@pytest.mark.asyncio
async def test_audit_system(client: AsyncClient):
    """审计日志 + 系统设置"""
    auth_resp = await client.post("/api/v1/auth/login", json={"password": settings.admin_password})
    token = auth_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 审计日志
    resp = await client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 200
    assert "items" in resp.json()["data"]

    resp = await client.get("/api/v1/audit-logs/stats", headers=headers)
    assert resp.status_code == 200

    # 系统入职规范
    resp = await client.get("/api/v1/system/onboarding", headers=headers)
    assert resp.status_code == 200

    resp = await client.put(
        "/api/v1/system/onboarding",
        json={"content": "# New Content"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["version"] >= 1
