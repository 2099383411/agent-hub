# Agent Hub Node.js SDK

智能体中台 Agent Node.js 接入 SDK。支持 REST API 和 MCP 两种接入方式。

## 安装

```bash
npm install agent-hub-sdk
```

## 快速开始

### REST API 方式

```javascript
const { AgentHubClient } = require('agent-hub-sdk');

const client = new AgentHubClient('http://192.168.1.100:8200', 'qw_abc123...', 'your_secret');

// 发送心跳
await client.heartbeat(
  { name: 'my-agent', type: 'generic', version: '1.0', mcp_supported: true },
  [{ name: 'pdf', version: '1.0.0', status: 'active' }],
  [{ name: 'nmap', version: '7.95' }]
);

// 获取技能列表
const skills = await client.listSkills();

// 下载技能包
const pkg = await client.downloadSkill('pdf');

// 搜索知识库
const results = await client.searchKnowledge('部署指南');
```

### MCP 方式

```javascript
const { MCPClient } = require('agent-hub-sdk');

const client = new MCPClient('http://192.168.1.100:8200', 'qw_abc123...', 'secret');
await client.connect();
const skills = await client.listSkills();
await client.close();
```

## API 参考

### AgentHubClient

| 方法 | 说明 |
|------|------|
| `heartbeat(agentInfo, installedSkills, availableTools)` | 发送心跳 |
| `listSkills()` | 获取可见技能列表 |
| `downloadSkill(name)` | 下载技能包 |
| `searchKnowledge(query, category)` | 搜索知识库 |

### MCPClient

| 方法 | 说明 |
|------|------|
| `connect()` | 建立连接 |
| `callTool(name, args)` | 调用 MCP tool |
| `listSkills()` | 获取技能列表 |
| `downloadSkill(name)` | 下载技能包 |
| `close()` | 断开连接 |

## 开发

```bash
npm install
npm test
```
