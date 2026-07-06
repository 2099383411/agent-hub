---
name: hub-connect
description: >
  Use this skill when the user wants to connect this agent to an Agent Hub
  (智能体中台). Triggered by phrases like "接入中台", "连接 Agent Hub",
  "配置中台", "connect to hub".
---

# Agent Hub 接入技能

## 何时触发
用户说"接入中台""连接 Agent Hub""配置中台"时触发。

## 接入流程

### 第一步：收集信息
向用户询问以下信息：
1. 中台地址（含端口，如 192.168.1.100:8200）
2. AppID（在中台 Web 面板创建 Agent 获取）
3. AppSecret

如果用户不知道，引导其：
1. 打开浏览器访问中台地址
2. 登录中台 Web 面板
3. 进入「Agent 管理」页面
4. 点击「创建 Agent」
5. 复制生成的 AppID 和 AppSecret

### 第二步：生成签名
AppSecret 不直接写入配置。按照中台签名算法生成 MCP 连接头：
```
签名串 = AppID + "\n" + "GET" + "\n" + "/mcp/sse" + "\n" + timestamp + "\n" + nonce
签名值 = HMAC-SHA256(AppSecret, 签名串)
```

### 第三步：写入 MCP 配置
找到本 Agent 的 MCP 配置文件，写入以下配置块：

```json
{
  "mcpServers": {
    "agent-hub": {
      "url": "http://{地址}/mcp/sse",
      "headers": {
        "X-Agent-AppID": "{AppID}",
        "X-Agent-Signature": "{生成的签名}"
      }
    }
  }
}
```

配置文件位置因 Agent 类型而异：
- QwenPaw: `~/.qwenpaw/workspaces/default/mcp.json`
- Claude Code: `~/.claude/mcp.json`
- Codex: `~/.codex/mcp.json`
- evolclaw: `~/.evolclaw/config.toml`
- 其他: 询问用户配置文件路径

### 第四步：验证并提示重启
配置写入后，告知用户：
```
配置已写入 {配置文件路径}。
请重启 Agent 使配置生效。
重启后 Agent 将自动连接中台，发现可用技能。
```
