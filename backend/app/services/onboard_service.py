"""一键接入服务"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent_service import AgentService
from app.utils.security import verify_onboard_token


ONBOARD_SCRIPT_TEMPLATE = """#!/bin/bash
# Agent Hub 一键接入脚本
set -e

HUB_ADDR="{hub_addr}"
TOKEN="{token}"

echo "🔍 正在获取接入信息..."
RESP=$(curl -s -X POST "$HUB_ADDR/api/v1/onboard/claim?token=$TOKEN")

APP_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['app_id'])")
APP_SECRET=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['app_secret'])")
AGENT_TYPE=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['agent_type'])" 2>/dev/null || echo "generic")

echo "✅ 接入成功！"
echo "  AppID: $APP_ID"
echo "  Agent 类型: $AGENT_TYPE"

# 写入 MCP 配置
echo "📝 正在写入 MCP 配置..."
MCP_CONFIG='{{
  "mcpServers": {{
    "agent-hub": {{
      "url": "'"$HUB_ADDR"'/mcp/sse",
      "headers": {{
        "X-Agent-AppID": "'"$APP_ID"'",
        "X-Agent-Signature": "'"$APP_SECRET"'"
      }}
    }}
  }}
}}'

# 检测 Agent 类型并找到配置路径
case "$AGENT_TYPE" in
  qwenpaw)
    CONFIG_DIR="$HOME/.qwenpaw/workspaces/default"
    mkdir -p "$CONFIG_DIR"
    echo "$MCP_CONFIG" > "$CONFIG_DIR/mcp.json"
    ;;
  claude_code)
    CONFIG_DIR="$HOME/.claude"
    mkdir -p "$CONFIG_DIR"
    echo "$MCP_CONFIG" > "$CONFIG_DIR/mcp.json"
    ;;
  codex)
    CONFIG_DIR="$HOME/.codex"
    mkdir -p "$CONFIG_DIR"
    echo "$MCP_CONFIG" > "$CONFIG_DIR/mcp.json"
    ;;
  evolclaw)
    echo "⚠️ evolclaw 请手动添加 MCP 配置到您的 agent 配置中"
    echo "$MCP_CONFIG"
    ;;
  *)
    echo "$MCP_CONFIG"
    ;;
esac

echo ""
echo "✅ 已接入 Agent Hub，请重启 Agent 生效"
echo "  中台地址: $HUB_ADDR"
echo "  AppID: $APP_ID"
"""


class OnboardService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_service = AgentService(db)

    async def generate_script(self, token: str, hub_addr: str) -> str | None:
        """生成一键接入脚本"""
        agent = await self.agent_service.get_agent_by_onboard_token(token)
        if not agent:
            return None

        now = agent.onboard_token_expires_at
        if not verify_onboard_token(token, agent.onboard_token, agent.onboard_token_expires_at):
            return None

        return ONBOARD_SCRIPT_TEMPLATE.format(hub_addr=hub_addr, token=token)

    async def claim_token(self, token: str, hub_addr: str = "") -> dict | None:
        """消耗 onboard token，返回 AppID 和 AppSecret"""
        agent = await self.agent_service.get_agent_by_onboard_token(token)
        if not agent:
            return None

        if not verify_onboard_token(token, agent.onboard_token, agent.onboard_token_expires_at):
            return None

        # 消耗 token
        agent.onboard_token = None
        agent.onboard_token_expires_at = None
        await self.db.commit()

        return {
            "app_id": agent.app_id,
            "app_secret": "",  # 安全考虑，实际需重新生成或预存
            "agent_type": agent.agent_type,
        }
