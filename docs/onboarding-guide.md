# Agent Hub 接入指南

## 三种接入方式

Agent Hub 提供递进式的三种接入方式：

```
一键命令（最简单）→ 对话技能（零门槛）→ 手动配置（最灵活）
```

### 方式一：一键命令接入（推荐）

在 Web 面板中创建 Agent 后复制一键命令，在 Agent 机器上执行：

```bash
curl -s http://<hub-addr>:8200/api/v1/onboard/claim?token=<TOKEN> | bash
```

脚本会自动：
1. 获取 AppID 和 AppSecret
2. 检测 Agent 类型（qwenpaw/claude_code/codex/evolclaw/generic）
3. 写入 MCP 配置文件
4. 提示重启 Agent

### 方式二：对话接入（hub-connect 技能）

如果 Agent 已安装了 hub-connect 预置技能，直接对 Agent 说：
> "帮我接入中台"

Agent 会引导完成接入流程。

### 方式三：手动配置 MCP

找到 Agent 的 MCP 配置文件，添加：

```json
{
  "mcpServers": {
    "agent-hub": {
      "url": "http://<hub-addr>:8200/mcp/sse",
      "headers": {
        "X-Agent-AppID": "<AppID>",
        "X-Agent-Signature": "<HMAC签名>"
      }
    }
  }
}
```

配置文件位置因 Agent 类型而异：

| Agent 类型 | 配置文件路径 |
|-----------|-------------|
| QwenPaw | `~/.qwenpaw/workspaces/default/mcp.json` |
| Claude Code | `~/.claude/mcp.json` |
| Codex | `~/.codex/mcp.json` |
| evolclaw | `~/.evolclaw/config.toml` |

## Agent 生命周期

```
创建 Agent → 获取 Onboard Token → 一键接入 → 
首次心跳（自动发现 pending skills）→ 
下载安装技能 → 定期心跳（合规检查）
```

### 心跳机制

- Agent 每 **30-60 秒** 发送一次心跳
- 心跳超时 **5 分钟** 标记为 `offline`
- 心跳返回：pending_skills + outdated_skills + compliance

### 合规检查

- 管理员可在 Web 面板设置「必装技能清单」
- Agent 心跳时自动检查必装技能安装情况
- 缺失必装技能的 Agent 标记为 `non_compliant`
- 合规状态在仪表盘实时展示

## MCP 工具列表

连接中台后，Agent 自动暴露以下 MCP tools：

| Tool | 用途 | 触发场景 |
|------|------|----------|
| `skills.list` | 发现可用技能 | Agent 启动 / 定时同步 |
| `skills.get` | 查看技能详情 | 选择安装时 |
| `skills.download` | 安装/更新技能 | 检测到新版本时 |
| `knowledge.search` | 搜索知识库 | 用户提问知识相关 |
| `knowledge.get` | 查看知识全文 | 需要详细内容时 |
| `hub.onboarding` | 获取工作规范 | 首次接入 / 版本更新 |

## 故障排除

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| MCP 连接失败 | 地址/端口错误 | 检查 hub_addr 和端口 |
| 401 认证失败 | AppID/Secret 错误 | 在 Web 面板重生成凭证 |
| 技能下载失败 | 技能被拉黑 | 在 Web 面板检查安检状态 |
| 心跳超时 | 网络不通 | 检查网络连通性 |
| 合规告警 | 缺少必装技能 | 安装缺失技能或申请豁免 |
