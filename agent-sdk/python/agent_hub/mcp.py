"""Agent Hub MCP 客户端（主力接入方式）"""

import json
import asyncio
from typing import Optional


class MCPAgentClient:
    """Agent Hub MCP 客户端（通过 SSE 连接 MCP Server）"""

    def __init__(self, hub_addr: str, app_id: str, app_secret: str):
        self.server_url = f"{hub_addr.rstrip('/')}/mcp/sse"
        self.app_id = app_id
        self.app_secret = app_secret
        self._reader = None
        self._writer = None
        self._connected = False
        self._session_id = None

    async def connect(self):
        """SSE 连接"""
        import httpx

        # 生成签名
        import time
        import hashlib
        import hmac
        import secrets

        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(8)
        message = f"{self.app_id}\nGET\n/mcp/sse\n{timestamp}\n{nonce}"
        signature = hmac.new(
            self.app_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        url = f"{self.server_url}?app_id={self.app_id}&timestamp={timestamp}&nonce={nonce}&signature={signature}"
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise ConnectionError(f"MCP 连接失败: {response.status_code}")
                self._connected = True
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "session_id":
                            self._session_id = data["session_id"]
                            break

    async def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """调用 MCP tool"""
        if not self._connected:
            raise RuntimeError("未连接 MCP Server")
        import httpx

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self.server_url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-AppID": self.app_id,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def list_skills(self) -> list[dict]:
        """获取技能列表（MCP）"""
        result = await self.call_tool("skills_list", {"scope": "public"})
        data = json.loads(result.get("result", "{}"))
        return data.get("skills", [])

    async def download_skill(self, name: str) -> dict | None:
        """下载技能包（MCP）"""
        result = await self.call_tool("skills_download", {"name": name})
        data = json.loads(result.get("result", "{}"))
        if "error" in data:
            return None
        return data

    async def search_knowledge(self, query: str) -> list[dict]:
        """搜索知识库（MCP）"""
        result = await self.call_tool("knowledge_search", {"query": query})
        data = json.loads(result.get("result", "{}"))
        return data.get("results", [])

    async def heartbeat(self, agent_info: dict, installed_skills: list[dict] = None):
        """心跳上报（MCP）"""
        data = {
            "agent_info": agent_info,
            "installed_skills": installed_skills or [],
        }
        result = await self.call_tool("agent_heartbeat", {"data": json.dumps(data)})
        return json.loads(result.get("result", "{}"))

    async def close(self):
        self._connected = False
