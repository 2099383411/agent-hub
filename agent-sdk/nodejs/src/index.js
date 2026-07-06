"use strict";

const axios = require("axios");
const crypto = require("crypto");

/**
 * Agent Hub Node.js Client
 * 支持 REST 和 MCP 两种接入方式
 */
class AgentHubClient {
  /**
   * @param {string} hubAddr - 中台地址 (http://host:port)
   * @param {string} appId - AppID
   * @param {string} appSecret - AppSecret
   */
  constructor(hubAddr, appId, appSecret) {
    this.baseURL = hubAddr.replace(/\/+$/, "");
    this.appId = appId;
    this.appSecret = appSecret;
    this.http = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        "X-Agent-AppID": appId,
        Authorization: `Bearer ${appSecret}`,
      },
    });
  }

  /**
   * 发送心跳
   * @param {Object} agentInfo - Agent 信息
   * @param {Array} [installedSkills] - 已安装技能
   * @param {Array} [availableTools] - 可用工具
   */
  async heartbeat(agentInfo, installedSkills = [], availableTools = []) {
    const res = await this.http.post("/api/v1/agent/heartbeat", {
      agent_info: agentInfo,
      installed_skills: installedSkills,
      available_tools: availableTools,
    });
    return res.data;
  }

  /** 获取可见技能列表 */
  async listSkills() {
    const res = await this.http.get("/api/v1/agent/skills");
    return res.data.skills || [];
  }

  /**
   * 下载技能包
   * @param {string} name - 技能名
   */
  async downloadSkill(name) {
    try {
      const res = await this.http.get(`/api/v1/agent/skills/${encodeURIComponent(name)}/download`);
      return res.data;
    } catch (err) {
      if (err.response?.status === 404) return null;
      throw err;
    }
  }

  /**
   * 搜索知识库
   * @param {string} query - 搜索关键词
   * @param {string} [category] - 分类筛选
   */
  async searchKnowledge(query, category) {
    const params = { q: query };
    if (category) params.category = category;
    const res = await this.http.get("/api/v1/agent/knowledge/search", { params });
    return res.data.results || [];
  }
}

/**
 * MCP 客户端（通过 SSE 连接）
 */
class MCPClient {
  /**
   * @param {string} hubAddr - 中台地址
   * @param {string} appId - AppID
   * @param {string} appSecret - AppSecret
   */
  constructor(hubAddr, appId, appSecret) {
    this.serverURL = `${hubAddr.replace(/\/+$/, "")}/mcp/sse`;
    this.appId = appId;
    this.appSecret = appSecret;
    this.sessionId = null;
    this.connected = false;
  }

  /** 生成 MCP 签名 */
  _sign() {
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const nonce = crypto.randomBytes(8).toString("hex");
    const message = `${this.appId}\nGET\n/mcp/sse\n${timestamp}\n${nonce}`;
    const signature = crypto
      .createHmac("sha256", this.appSecret)
      .update(message)
      .digest("hex");
    return { timestamp, nonce, signature };
  }

  /** 建立 SSE 连接 */
  async connect() {
    // Node.js 没有原生 SSE 客户端，用 EventSource 或 fetch
    const { timestamp, nonce, signature } = this._sign();
    const url = `${this.serverURL}?app_id=${this.appId}&timestamp=${timestamp}&nonce=${nonce}&signature=${signature}`;
    
    // HTTP POST 调用（简化版）
    this.httpClient = axios.create({
      baseURL: this.serverURL.replace("/mcp/sse", ""),
      timeout: 60000,
      headers: { "X-Agent-AppID": this.appId },
    });
    this.connected = true;
  }

  /**
   * 调用 MCP tool
   * @param {string} toolName - 工具名
   * @param {Object} args - 参数
   */
  async callTool(toolName, args = {}) {
    if (!this.connected) throw new Error("MCP 未连接");
    const res = await this.httpClient.post("/mcp/sse", {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: { name: toolName, arguments: args },
    });
    return res.data;
  }

  /** 获取技能列表 */
  async listSkills() {
    const result = await this.callTool("skills_list", { scope: "public" });
    const data = typeof result.result === "string" ? JSON.parse(result.result) : result.result;
    return data.skills || [];
  }

  /** 下载技能包 */
  async downloadSkill(name) {
    const result = await this.callTool("skills_download", { name });
    const data = typeof result.result === "string" ? JSON.parse(result.result) : result.result;
    if (data.error) return null;
    return data;
  }

  async close() {
    this.connected = false;
  }
}

module.exports = { AgentHubClient, MCPClient };
