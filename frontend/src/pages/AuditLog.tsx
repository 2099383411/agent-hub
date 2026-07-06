import { useState, useEffect } from 'react';
import { Table, Tag, Card, Typography, Select, Space, Statistic, Row, Col } from 'antd';
import { auditApi } from '../api/client';
import dayjs from 'dayjs';

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  'agent.create': { label: '创建 Agent', color: 'green' },
  'agent.delete': { label: '删除 Agent', color: 'red' },
  'agent.regenerate': { label: '重生成凭证', color: 'orange' },
  'skill.upload': { label: '上传技能', color: 'blue' },
  'skill.assign': { label: '分配技能', color: 'purple' },
  'skill.unassign': { label: '取消分配', color: 'default' },
  'skill.delete': { label: '删除技能', color: 'red' },
  'skill.block': { label: '拉黑技能', color: 'red' },
  'skill.import': { label: '导入技能', color: 'cyan' },
  'knowledge.create': { label: '创建知识', color: 'green' },
  'knowledge.delete': { label: '删除知识', color: 'red' },
};

export default function AuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [total, setTotal] = useState(0);

  const load = async (action?: string) => {
    setLoading(true);
    try {
      const params: any = { page: 1, page_size: 100 };
      if (action) params.action = action;
      const [logRes, statsRes]: any[] = await Promise.all([
        auditApi.list(params),
        auditApi.stats(),
      ]);
      setLogs(logRes.data?.items || []);
      setTotal(logRes.data?.total || 0);
      setStats(statsRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleFilterChange = (value: string) => {
    setActionFilter(value);
    load(value || undefined);
  };

  const columns = [
    {
      title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作', dataIndex: 'action', key: 'action', width: 140,
      render: (a: string) => {
        const info = ACTION_LABELS[a] || { label: a, color: 'default' };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    { title: '操作者', dataIndex: 'actor', key: 'actor', width: 100 },
    { title: '目标', dataIndex: 'target', key: 'target', ellipsis: true },
    { title: '详情', dataIndex: 'details', key: 'details', ellipsis: true },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip_address', width: 140 },
  ];

  return (
    <div>
      <Typography.Title level={4}>审计日志</Typography.Title>

      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Card><Statistic title="总日志数" value={stats.total_logs} /></Card></Col>
          <Col span={6}><Card><Statistic title="近 24 小时" value={stats.recent_24h} valueStyle={{ color: '#1677ff' }} /></Card></Col>
        </Row>
      )}

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Typography.Text>操作类型：</Typography.Text>
          <Select
            style={{ width: 200 }}
            value={actionFilter}
            onChange={handleFilterChange}
            allowClear
            placeholder="全部操作"
            options={Object.entries(ACTION_LABELS).map(([value, info]) => ({
              value,
              label: info.label,
            }))}
          />
        </Space>
      </Card>

      <Table
        dataSource={logs}
        columns={columns}
        rowKey="id"
        loading={loading}
        size="small"
        pagination={{ total, pageSize: 50, showSizeChanger: false }}
      />
    </div>
  );
}
