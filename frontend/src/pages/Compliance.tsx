import { useState, useEffect } from 'react';
import { Table, Tag, Card, Typography, Spin } from 'antd';
import { complianceApi } from '../api/client';

export default function Compliance() {
  const [data, setData] = useState<any[]>([]);
  const [mandatory, setMandatory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([complianceApi.status(), complianceApi.mandatory()])
      .then(([statusRes, manRes]: any[]) => {
        setData(statusRes.data || []);
        setMandatory(manRes.data || []);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const columns = [
    { title: 'Agent', dataIndex: 'agent_name', key: 'agent_name' },
    {
      title: '合规状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'compliant' ? 'green' : 'red'}>{s === 'compliant' ? '✅ 合规' : '⚠️ 不合规'}</Tag>,
    },
    { title: '缺失必装技能', dataIndex: 'missing_mandatory', key: 'missing_mandatory', render: (v: string[]) => v.length > 0 ? v.join(', ') : <Tag color="green">无</Tag> },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Typography.Title level={5}>必装技能清单</Typography.Title>
        {mandatory.length === 0 ? (
          <Typography.Text type="secondary">暂无必装技能</Typography.Text>
        ) : (
          <ul>
            {mandatory.map((m: any) => <li key={m.id}><strong>{m.name}</strong> v{m.version}</li>)}
          </ul>
        )}
      </Card>

      <Card title="Agent 合规状态矩阵">
        <Table dataSource={data} columns={columns} rowKey="agent_id" pagination={false} size="small" />
      </Card>
    </div>
  );
}
