const assert = require('assert');
const { AgentHubClient, MCPClient } = require('../src/index.js');

describe('AgentHubClient', () => {
  it('should create client with correct config', () => {
    const client = new AgentHubClient('http://localhost:8200', 'qw_test', 'secret123');
    assert.strictEqual(client.baseURL, 'http://localhost:8200');
    assert.strictEqual(client.appId, 'qw_test');
    assert.strictEqual(client.appSecret, 'secret123');
  });

  it('should strip trailing slash from hub address', () => {
    const client = new AgentHubClient('http://localhost:8200/', 'qw_test', 'secret');
    assert.strictEqual(client.baseURL, 'http://localhost:8200');
  });

  it('should have all required methods', () => {
    const client = new AgentHubClient('http://localhost:8200', 'qw_test', 'secret');
    assert.strictEqual(typeof client.heartbeat, 'function');
    assert.strictEqual(typeof client.listSkills, 'function');
    assert.strictEqual(typeof client.downloadSkill, 'function');
    assert.strictEqual(typeof client.searchKnowledge, 'function');
  });
});

describe('MCPClient', () => {
  it('should create MCP client with correct config', () => {
    const client = new MCPClient('http://localhost:8200', 'qw_test', 'secret');
    assert.strictEqual(client.serverURL, 'http://localhost:8200/mcp/sse');
    assert.strictEqual(client.appId, 'qw_test');
    assert.strictEqual(client.connected, false);
  });

  it('should have _sign method generating valid signature', () => {
    const client = new MCPClient('http://localhost:8200', 'qw_test', 'secret');
    const { timestamp, nonce, signature } = client._sign();
    assert(timestamp.length > 0);
    assert(nonce.length > 0);
    assert.strictEqual(signature.length, 64);
  });

  it('should have all required methods', () => {
    const client = new MCPClient('http://localhost:8200', 'qw_test', 'secret');
    assert.strictEqual(typeof client.connect, 'function');
    assert.strictEqual(typeof client.callTool, 'function');
    assert.strictEqual(typeof client.listSkills, 'function');
    assert.strictEqual(typeof client.downloadSkill, 'function');
    assert.strictEqual(typeof client.close, 'function');
  });
});
