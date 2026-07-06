# Agent Hub API 文档

## 概述

API 基地址：`http://<hub-addr>:8200/api/v1`

所有管理接口需要 JWT 认证（`Authorization: Bearer <token>`）。
Agent 接口需要 HMAC 签名或 Bearer Token 认证。

## 认证

### 管理员登录

```
POST /api/v1/auth/login
Content-Type: application/json

{"password": "admin123"}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

## Agent 管理

### 创建 Agent

```
POST /api/v1/agents
Authorization: Bearer <token>
Content-Type: application/json

{"agent_name": "my-agent", "agent_type": "generic"}

Response:
{
  "code": 0,
  "data": {
    "agent": {
      "id": "uuid...",
      "agent_name": "my-agent",
      "agent_type": "generic",
      "app_id": "qw_abc...",
      "status": "offline"
    },
    "app_id": "qw_abc...",
    "app_secret": "...",
    "onboard_command": "curl -s ... | bash"
  }
}
```

### 列表 / 详情 / 删除

```
GET    /api/v1/agents                  # 列表
GET    /api/v1/agents/{id}              # 详情
DELETE /api/v1/agents/{id}              # 删除
POST   /api/v1/agents/{id}/regenerate-credential  # 重生成凭证
```

## 技能管理

### 上传技能

```
POST /api/v1/skills/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <SKILL.md>
scope: public|private
is_mandatory: true|false
```

上传即自动触发 Tier 1 静态分析扫描。

### CRUD

```
GET    /api/v1/skills                   # 列表
GET    /api/v1/skills/{id}              # 详情
PUT    /api/v1/skills/{id}              # 更新 scope/mandatory
DELETE /api/v1/skills/{id}              # 删除
POST   /api/v1/skills/{id}/assign      # 分配
POST   /api/v1/skills/{id}/unassign    # 取消分配
POST   /api/v1/skills/{id}/block       # 拉黑
```

## 合规 / 审计 / 仪表盘

```
GET /api/v1/compliance/status           # 全局合规状态
GET /api/v1/compliance/mandatory        # 必装技能列表
GET /api/v1/audit-logs                  # 审计日志列表
GET /api/v1/audit-logs/stats            # 审计统计
GET /api/v1/dashboard/overview          # 总览仪表盘
```

## Agent REST API（兜底）

### 心跳上报

```
POST /api/v1/agent/heartbeat
X-Agent-AppID: qw_abc...
Authorization: Bearer <secret>

{
  "agent_info": {"name":"my-agent","type":"generic","version":"1.0"},
  "installed_skills": [{"name":"pdf","version":"1.0.0","status":"active"}],
  "available_tools": [{"name":"nmap","version":"7.95","path":"/usr/bin/nmap"}]
}
```

### 技能 / 知识（Agent 视角）

```
GET /api/v1/agent/skills                          # 可见技能列表
GET /api/v1/agent/skills/{name}/download          # 下载技能包
GET /api/v1/agent/knowledge/search?q=部署指南      # 搜索知识库
```

## 错误码

| 状态码 | 含义 | 处理方式 |
|--------|------|----------|
| 200 | 成功 | — |
| 400 | 请求参数错误 | 检查请求体 |
| 401 | 未认证 / Token 过期 | 重新登录 |
| 404 | 资源不存在 | 检查 ID |
| 500 | 服务端错误 | 查看日志重试 |
