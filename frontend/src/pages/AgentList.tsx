import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, message, Popconfirm, Typography, Tooltip } from 'antd';
import { PlusOutlined, KeyOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { agentApi } from '../api/client';

export default function AgentList() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<any>(null);
  const [onboardCommand, setOnboardCommand] = useState<string>('');
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res: any = await agentApi.list();
      setAgents(res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const fetchOnboardToken = async (agentId: string) => {
    try {
      const res: any = await agentApi.refreshToken(agentId);
      // token 通过 command 隐含携带
      setOnboardCommand(res.data.onboard_command);
    } catch {
      // 清空
      setOnboardCommand('');
    }
  };

  const onCreate = async (values: any) => {
    const res: any = await agentApi.create(values);
    message.success('Agent 创建成功');
    setCreateOpen(false);
    form.resetFields();
    const data = res.data;
    setCurrentAgent(data.agent || data);
    setOnboardCommand(data.onboard_command || '');
    setDetailOpen(true);
    load();
  };

  const onDelete = async (id: string) => {
    await agentApi.delete(id);
    message.success('已删除');
    load();
  };

  const onRegenerate = async (record: any) => {
    try {
      const res: any = await agentApi.regenerate(record.id);
      message.success('凭证已重新生成');
      await load();
      setCurrentAgent({ ...record, app_id: res.data.app_id, app_secret: res.data.app_secret });
      // 同时刷新 onboard token
      await fetchOnboardToken(record.id);
      setDetailOpen(true);
    } catch (err: any) {
      message.error(err.response?.data?.detail || '重生成凭证失败');
    }
  };

  const onViewDetail = async (record: any) => {
    setCurrentAgent(record);
    // 打开指引时自动获取最新的 onboard token
    await fetchOnboardToken(record.id);
    setDetailOpen(true);
  };

  const columns: any[] = [
    { title: '名称', dataIndex: 'agent_name', key: 'agent_name' },
    { title: '类型', dataIndex: 'agent_type', key: 'agent_type', width: 100 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (s: string) => <Tag color={s === 'online' ? 'green' : 'default'}>{s === 'online' ? '在线' : '离线'}</Tag>,
    },
    { title: 'AppID', dataIndex: 'app_id', key: 'app_id', ellipsis: true },
    { title: 'IP', dataIndex: 'host_ip', key: 'host_ip', width: 120 },
    { title: '最后心跳', dataIndex: 'last_heartbeat_at', key: 'last_heartbeat_at', width: 160, render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    {
      title: '操作', key: 'action', width: 220, align: 'left',
      render: (_: any, record: any) => (
        <span>
          <Tooltip title="查看接入指引">
            <Button size="small" type="link" icon={<EyeOutlined />} style={{ paddingLeft: 0 }} onClick={() => onViewDetail(record)}>接入</Button>
          </Tooltip>
          <Tooltip title="重新生成 AppID 和 AppSecret">
            <Button size="small" type="link" icon={<KeyOutlined />} onClick={() => onRegenerate(record)}>凭证</Button>
          </Tooltip>
          <Popconfirm title="确定删除此 Agent？" onConfirm={() => onDelete(record.id)}>
            <Button size="small" type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </span>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Agent 管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建 Agent</Button>
      </div>

      <Table
        dataSource={agents}
        columns={columns}
        rowKey="id"
        loading={loading}
        size="small"
        pagination={{ pageSize: 20 }}
        scroll={{ x: 900 }}
      />

      <Modal title="创建 Agent" open={createOpen} onOk={() => form.submit()} onCancel={() => { setCreateOpen(false); form.resetFields(); }}>
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item name="agent_name" label="名称" rules={[{ required: true }]}>
            <Input placeholder="例如：小灵" />
          </Form.Item>
          <Form.Item name="agent_type" label="类型" initialValue="generic">
            <Select options={[
              { value: 'qwenpaw', label: 'QwenPaw' },
              { value: 'evolclaw', label: 'EvolClaw' },
              { value: 'claude_code', label: 'Claude Code' },
              { value: 'codex', label: 'Codex' },
              { value: 'generic', label: '通用' },
            ]} />
          </Form.Item>
          <Form.Item name="host_ip" label="主机 IP">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="接入指引" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={640}>
        {currentAgent && (
          <div>
            <Typography.Paragraph>
              <strong>名称：</strong> {currentAgent.agent_name}<br />
              <strong>AppID：</strong>
              <Typography.Text copyable>{currentAgent.app_id}</Typography.Text>
              <br />
              {currentAgent.app_secret && (
                <>
                  <strong>AppSecret：</strong>
                  <Typography.Text copyable={{ text: currentAgent.app_secret }}>{currentAgent.app_secret}</Typography.Text>
                  <br />
                </>
              )}
            </Typography.Paragraph>

            <Typography.Title level={5}>方式一：一键命令接入</Typography.Title>
            <Typography.Paragraph>在 Agent 所在机器上执行以下命令：</Typography.Paragraph>
            {onboardCommand ? (
              <Typography.Paragraph copyable={{ text: onboardCommand }}>
                <code style={{ background: '#f5f5f5', padding: '8px', display: 'block', borderRadius: 4, fontSize: 12, wordBreak: 'break-all' }}>
                  {onboardCommand}
                </code>
              </Typography.Paragraph>
            ) : (
              <Typography.Text type="secondary">（生成命令失败，请尝试重生成凭证）</Typography.Text>
            )}

            <Typography.Title level={5}>方式二：手动 MCP 配置</Typography.Title>
            <Typography.Paragraph>在 Agent 的 MCP 配置文件中添加：</Typography.Paragraph>
            <Typography.Paragraph copyable>
              <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, fontSize: 12, overflow: 'auto' }}>
                {JSON.stringify({
                  mcpServers: {
                    'agent-hub': {
                      url: `http://${window.location.hostname}:8200/mcp/sse`,
                      headers: { 'X-Agent-AppID': currentAgent.app_id },
                    },
                  },
                }, null, 2)}
              </pre>
            </Typography.Paragraph>
          </div>
        )}
      </Modal>
    </div>
  );
}
