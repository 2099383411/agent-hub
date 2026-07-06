import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin, Table, Tag } from 'antd';
import { RobotOutlined, AppstoreOutlined, SafetyCertificateOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { dashboardApi, complianceApi } from '../api/client';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [compliance, setCompliance] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      dashboardApi.overview(),
      complianceApi.status(),
    ]).then(([overviewRes, compRes]: any[]) => {
      setData(overviewRes.data);
      setCompliance(compRes.data || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const complianceColumns = [
    { title: 'Agent', dataIndex: 'agent_name', key: 'agent_name' },
    {
      title: '合规状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'compliant' ? 'green' : 'red'}>{s === 'compliant' ? '✅ 合规' : '⚠️ 不合规'}</Tag>,
    },
    { title: '缺失必装技能', dataIndex: 'missing_mandatory', key: 'missing_mandatory', render: (v: string[]) => v.join(', ') || '无' },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="Agent 总数" value={data?.agents?.total || 0} prefix={<RobotOutlined />} suffix={<span style={{ fontSize: 14, color: '#999' }}>/ 在线 {data?.agents?.online || 0}</span>} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="技能总数" value={data?.skills?.total || 0} prefix={<AppstoreOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="合规率" value={data?.compliance?.compliance_rate || 0} suffix="%" prefix={<CheckCircleOutlined />} valueStyle={{ color: (data?.compliance?.compliance_rate || 0) >= 80 ? '#3f8600' : '#cf1322' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="高风险技能" value={data?.security?.high_risk_skills || 0} prefix={<SafetyCertificateOutlined />} valueStyle={{ color: '#cf1322' }} /></Card>
        </Col>
      </Row>

      <Card title="Agent 合规状态">
        <Table
          dataSource={compliance}
          columns={complianceColumns}
          rowKey="agent_id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}
