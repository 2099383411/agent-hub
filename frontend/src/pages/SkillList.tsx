import { useState, useEffect } from 'react';
import { Table, Button, Modal, Upload, Select, Tag, Space, message, Popconfirm, Typography } from 'antd';
import { UploadOutlined, LinkOutlined, BlockOutlined, DeleteOutlined } from '@ant-design/icons';
import { skillApi, agentApi } from '../api/client';

export default function SkillList() {
  const [skills, setSkills] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [currentSkill, setCurrentSkill] = useState<any>(null);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const [sRes, aRes]: any[] = await Promise.all([skillApi.list(), agentApi.list()]);
      setSkills(sRes.data?.skills || []);
      setAgents(aRes.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async (file: File) => {
    try {
      const res: any = await skillApi.upload(file);
      message.success(res.data?.message || '上传成功');
      load();
    } catch (err: any) {
      message.error('上传失败');
    }
    return false;
  };

  const handleAssign = async () => {
    if (!currentSkill) return;
    await skillApi.assign(currentSkill.id, selectedAgents);
    message.success('分配成功');
    setAssignOpen(false);
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '分类', dataIndex: 'category', key: 'category' },
    {
      title: '范围', dataIndex: 'scope', key: 'scope',
      render: (s: string) => <Tag>{s === 'public' ? '🌐 公开' : '🔒 私有'}</Tag>,
    },
    {
      title: '安全状态', dataIndex: 'security_status', key: 'security_status',
      render: (s: string, r: any) => {
        const colorMap: any = { passed: 'green', warning: 'orange', pending: 'default', blocked: 'red' };
        return <Tag color={colorMap[s] || 'default'}>{r.security_risk_level ? `${r.security_risk_level}` : s}</Tag>;
      },
    },
    {
      title: '必装', dataIndex: 'is_mandatory', key: 'is_mandatory',
      render: (v: boolean) => v ? <Tag color="blue">必装</Tag> : '-',
    },
    {
      title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<LinkOutlined />} onClick={() => { setCurrentSkill(record); setAssignOpen(true); }}>分配</Button>
          <Popconfirm title="设为私有后 Agent 不可自发现" onConfirm={() => skillApi.update(record.id, { scope: record.scope === 'public' ? 'private' : 'public' }).then(load)}>
            <Button type="link">{record.scope === 'public' ? '设私有' : '设公开'}</Button>
          </Popconfirm>
          <Popconfirm title="确定拉黑此技能？" onConfirm={() => skillApi.block(record.id).then(() => { message.success('已拉黑'); load(); })}>
            <Button type="link" danger icon={<BlockOutlined />}>拉黑</Button>
          </Popconfirm>
          <Popconfirm title="确定删除？" onConfirm={() => skillApi.delete(record.id).then(load)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>技能库</Typography.Title>
        <Upload beforeUpload={handleUpload} showUploadList={false} accept=".md,.yaml,.yml">
          <Button type="primary" icon={<UploadOutlined />}>上传技能</Button>
        </Upload>
      </div>

      <Table dataSource={skills} columns={columns} rowKey={(r) => r.name} loading={loading} size="small" />

      <Modal title="分配技能" open={assignOpen} onOk={handleAssign} onCancel={() => setAssignOpen(false)}>
        <Typography.Paragraph>将技能 <strong>{currentSkill?.name}</strong> 分配给以下 Agent：</Typography.Paragraph>
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="选择 Agent"
          value={selectedAgents}
          onChange={setSelectedAgents}
          options={agents.map((a: any) => ({ value: a.id, label: a.agent_name }))}
        />
      </Modal>
    </div>
  );
}
