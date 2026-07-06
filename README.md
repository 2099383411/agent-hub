# Agent Hub（智能体中台）

**局域网级的智能体资产中台** — 技能仓库 + 安检流水线 + 入职手册，三合一。

## 产品定位

Agent Hub 不做 Agent 间的任务协作调度，只做三件事：

1. **技能统一管理** — 装一次，所有 Agent 自动发现并使用
2. **安全统一检测** — 技能导入即扫描，风险可追溯
3. **知识统一分发** — 入职手册、开发规范一次录入，全 Agent 共享

## 快速开始

### 启动服务

```bash
# 克隆仓库
git clone <repo-url>
cd agent-hub

# 启动（Docker Compose）
docker-compose up -d

# 访问 Web 面板
# http://localhost:8201

# 默认管理员密码：admin123
```

### 一键接入 Agent

```bash
curl -s http://localhost:8200/api/v1/onboard/claim?token=<TOKEN> | bash
```

或者在 Web 面板中：
1. 进入「Agent 管理」→ 创建 Agent
2. 复制一键接入命令
3. 在 Agent 所在机器上执行

## 核心功能

### Web 面板（端口 8201）

| 页面 | 功能 |
|------|------|
| 📊 仪表盘 | Agent/技能/合规/安全总览 |
| 🤖 Agent 管理 | 创建/删除/查看 Agent，凭证管理 |
| 📦 技能库 | 上传/分配/公开私有切换 |
| 🌐 公共市场 | ClawHub / SkillHub 搜索导入 |
| 🛡️ 安检中心 | 扫描记录 / Tier 1 & Tier 2 安检 |
| ✅ 合规检查 | 必装技能清单 + 缺失告警 |
| 📋 审计日志 | 全操作审计追溯 |
| 📚 知识库 | 入职手册 / 开发规范管理 |

### MCP 协议（主力接入方式）

| Tool | 说明 |
|------|------|
| `skills.list` | 获取技能列表 |
| `skills.get` | 查看技能详情 |
| `skills.download` | 下载技能包 |
| `agent.heartbeat` | Agent 心跳上报 |
| `knowledge.search` | 搜索知识库 |
| `knowledge.get` | 获取知识条目全文 |
| `hub.onboarding` | 获取中台使用规范 |

### REST API（兜底）

| 端点 | 说明 |
|------|------|
| `POST /api/v1/agent/heartbeat` | 心跳上报 |
| `GET /api/v1/agent/skills` | 技能列表 |
| `GET /api/v1/agent/skills/{name}/download` | 下载技能包 |
| `GET /api/v1/agent/knowledge/search` | 搜索知识库 |

## 安全检测体系

| 等级 | 方式 | 说明 |
|------|------|------|
| Tier 1 | 静态分析 | 正则匹配危险模式（shell/网络/文件/提权等） |
| Tier 2 | 沙箱执行 | Docker 隔离执行，动态行为检测 |
| Tier 3 | 威胁建模 | 预留 |

## 技术栈

- **后端**：Python FastAPI + SQLAlchemy + SQLite + MCP (FastMCP)
- **前端**：React + TypeScript + Ant Design
- **部署**：Docker Compose
- **SDK**：Python / Node.js

## 项目结构

```
agent-hub/
├── backend/              后端服务 (FastAPI + MCP)
│   ├── app/
│   │   ├── api/           REST API 路由
│   │   ├── services/      业务逻辑层
│   │   ├── models/        SQLAlchemy 模型
│   │   ├── schemas/       Pydantic 数据模型
│   │   ├── mcp/           MCP Server
│   │   └── utils/         工具函数
│   └── tests/             测试套件（85 个测试）
├── frontend/              Web 管理面板 (React + Ant Design)
├── agent-sdk/             Agent 接入 SDK
│   ├── python/            Python SDK
│   └── nodejs/            Node.js SDK
├── docker-compose.yml     部署配置
└── 开发文档/               PRD 与技术方案
```

## 开发规范

- 遵循 RESTful API 设计规范
- 代码整洁、模块化、可维护性优先
- 先测试再实现，所有新功能必须有单元测试
- 遵守《阿里巴巴 Java 开发手册》思路（Python 版）

## 许可证

MIT
