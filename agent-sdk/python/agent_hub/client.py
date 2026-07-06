"""Agent Hub REST API 客户端（兜底方式，不支持 MCP 时使用）"""

import asyncio
import hmac
import hashlib
import time
import secrets
from dataclasses import dataclass, field
from typing import Optional

import httpx


@dataclass
class InstalledSkill:
    name: str
    version: str
    status: str = "active"


@dataclass
class ToolInfo:
    name: str
    version: Optional[str] = None
    path: Optional[str] = None


@dataclass
class AgentInfo:
    name: str
    type: str = "generic"
    version: Optional[str] = None
    host_ip: Optional[str] = None
    mcp_supported: bool = True


class AgentHubClient:
    """Agent Hub REST 客户端（不用 MCP 时的兜底方案）

    特性：
    - 自动重试（3 次，指数退避）
    - 请求超时 30s
    - HMAC 签名鉴权
    - 完整的错误处理
    """

    def __init__(self, hub_addr: str, app_id: str, app_secret: str, max_retries: int = 3):
        self.base_url = hub_addr.rstrip("/")
        self.app_id = app_id
        self.app_secret = app_secret
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-Agent-AppID": app_id,
                "Authorization": f"Bearer {app_secret}",
            },
            timeout=30,
        )

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """带重试的 HTTP 请求"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = await self._client.request(method, path, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except httpx.HTTPStatusError as e:
                if 500 <= e.response.status_code < 600 and attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
            except (httpx.RequestError, httpx.TransportError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"请求失败（重试 {self.max_retries} 次后）: {last_error}") from last_error
        raise RuntimeError(f"请求失败（重试 {self.max_retries} 次后）: {last_error}") from last_error

    async def heartbeat(
        self,
        agent_info: AgentInfo,
        installed_skills: list[InstalledSkill] | None = None,
        available_tools: list[ToolInfo] | None = None,
    ) -> dict:
        """发送心跳"""
        data = {
            "agent_info": {
                "name": agent_info.name,
                "type": agent_info.type,
                "version": agent_info.version,
                "host_ip": agent_info.host_ip,
                "mcp_supported": agent_info.mcp_supported,
            },
            "installed_skills": [
                {"name": s.name, "version": s.version, "status": s.status}
                for s in (installed_skills or [])
            ],
            "available_tools": [
                {"name": t.name, "version": t.version, "path": t.path}
                for t in (available_tools or [])
            ],
        }
        return await self._request("POST", "/api/v1/agent/heartbeat", json=data)

    async def list_skills(self) -> list[dict]:
        """获取可见技能列表"""
        data = await self._request("GET", "/api/v1/agent/skills")
        return data.get("skills", [])

    async def download_skill(self, name: str) -> dict | None:
        """下载技能包（404 时返回 None）"""
        try:
            return await self._request("GET", f"/api/v1/agent/skills/{name}/download")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def search_knowledge(self, query: str, category: str = None) -> list[dict]:
        """搜索知识库"""
        params = {"q": query}
        if category:
            params["category"] = category
        data = await self._request("GET", "/api/v1/agent/knowledge/search", params=params)
        return data.get("results", [])

    @staticmethod
    def generate_mcp_signature(app_id: str, app_secret: str) -> tuple[str, str, str]:
        """生成 MCP 握手签名（工具方法）"""
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(8)
        message = f"{app_id}\nGET\n/mcp/sse\n{timestamp}\n{nonce}"
        signature = hmac.new(app_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        return timestamp, nonce, signature

    async def close(self):
        await self._client.aclose()
