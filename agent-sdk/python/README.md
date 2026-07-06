# Agent Hub Python SDK

智能体中台 Agent Python 接入 SDK。支持 REST API 和 MCP 两种接入方式。

## 安装

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple agent-hub-sdk
```

或从源码安装：

```bash
cd agent-sdk/python
pip install .
```

## 快速开始

### REST API 方式（兜底）

```python
from agent_hub import AgentHubClient, AgentInfo, InstalledSkill, ToolInfo

# 创建客户端
client = AgentHubClient(
    hub_addr="http://192.168.1.100:8200",
    app_id="qw_abc123...",
    app_secret="your_secret_key",
)

# 发送心跳
resp = await client.heartbeat(
    agent_info=AgentInfo(name="my-agent", type="generic", version="1.0"),
    installed_skills=[InstalledSkill(name="pdf", version="1.0.0")],
    available_tools=[ToolInfo(name="nmap", version="7.95")],
)

# 获取技能列表
skills = await client.list_skills()

# 下载技能包
pkg = await client.download_skill("pdf")
if pkg:
    for file in pkg["files"]:
        print(f"  {file['path']} ({file['size_bytes']} bytes)")

# 搜索知识库
results = await client.search_knowledge("部署指南")

# 关闭连接
await client.close()
```

### MCP 方式（主力）

```python
from agent_hub import MCPAgentClient

client = MCPAgentClient(
    hub_addr="http://192.168.1.100:8200",
    app_id="qw_abc123...",
    app_secret="your_secret_key",
)

await client.connect()
skills = await client.list_skills()
await client.close()
```

## API 参考

### AgentHubClient

| 方法 | 说明 |
|------|------|
| `heartbeat(agent_info, installed_skills, available_tools)` | 发送心跳 |
| `list_skills()` | 获取可见技能列表 |
| `download_skill(name)` | 下载技能包 |
| `search_knowledge(query, category)` | 搜索知识库 |
| `generate_mcp_signature(app_id, app_secret)` | 生成 MCP 签名 |
| `close()` | 关闭客户端 |

### MCPAgentClient

| 方法 | 说明 |
|------|------|
| `connect()` | 建立 SSE 连接 |
| `call_tool(name, arguments)` | 调用 MCP tool |
| `list_skills()` | 获取技能列表 |
| `download_skill(name)` | 下载技能包 |
| `search_knowledge(query)` | 搜索知识库 |
| `heartbeat(agent_info, installed_skills)` | 心跳上报 |
| `close()` | 断开连接 |

## 错误处理

- 网络错误：自动重试 3 次（指数退避）
- HTTP 4xx：直接抛出异常
- HTTP 5xx：重试 3 次后抛出
- 404：`download_skill` 返回 None

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/
```
