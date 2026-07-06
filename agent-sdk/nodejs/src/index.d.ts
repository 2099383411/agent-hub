export interface AgentInfo {
  name: string;
  type?: string;
  version?: string;
  host_ip?: string;
  mcp_supported?: boolean;
}

export interface InstalledSkill {
  name: string;
  version: string;
  status?: string;
}

export interface ToolInfo {
  name: string;
  version?: string;
  path?: string;
}

export class AgentHubClient {
  constructor(hubAddr: string, appId: string, appSecret: string);
  heartbeat(agentInfo: AgentInfo, installedSkills?: InstalledSkill[], availableTools?: ToolInfo[]): Promise<any>;
  listSkills(): Promise<any[]>;
  downloadSkill(name: string): Promise<any | null>;
  searchKnowledge(query: string, category?: string): Promise<any[]>;
}

export class MCPClient {
  constructor(hubAddr: string, appId: string, appSecret: string);
  connect(): Promise<void>;
  callTool(toolName: string, args?: any): Promise<any>;
  listSkills(): Promise<any[]>;
  downloadSkill(name: string): Promise<any | null>;
  close(): Promise<void>;
}
