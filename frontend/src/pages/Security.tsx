import { useState, useEffect } from 'react';
import { Table, Tag, Card, Typography, Spin, Descriptions, Modal, Button } from 'antd';
import { securityApi } from '../api/client';
import { EyeOutlined } from '@ant-design/icons';

export default function Security() {
  const [scans, setScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailOpen, setDetailOpen] = useState(false);
  const [currentScan, setCurrentScan] = useState<any>(null);

  useEffect(() => {
    securityApi.listScans().then((res: any) => {
      setScans(res.data || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const riskColor: any = { high: 'red', medium: 'orange', low: 'yellow', none: 'green' };

  const columns = [
    { title: '技能 ID', dataIndex: 'skill_id', key: 'skill_id', ellipsis: true },
    { title: '扫描类型', dataIndex: 'scan_type', key: 'scan_type' },
    {
      title: '风险等级', dataIndex: 'risk_level', key: 'risk_level',
      render: (v: string) => <Tag color={riskColor[v] || 'default'}>{v}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag>{s === 'completed' ? '✅ 完成' : s}</Tag>,
    },
    {
      title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => { setCurrentScan(record); setDetailOpen(true); }}>
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>安检中心</Typography.Title>
      <Table dataSource={scans} columns={columns} rowKey="id" size="small" />

      <Modal title="扫描详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={640}>
        {currentScan && (
          <div>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="技能 ID">{currentScan.skill_id}</Descriptions.Item>
              <Descriptions.Item label="扫描类型">{currentScan.scan_type}</Descriptions.Item>
              <Descriptions.Item label="风险等级"><Tag color={riskColor[currentScan.risk_level]}>{currentScan.risk_level}</Tag></Descriptions.Item>
              <Descriptions.Item label="状态">{currentScan.status}</Descriptions.Item>
            </Descriptions>
            {currentScan.findings?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Typography.Title level={5}>检出项</Typography.Title>
                {currentScan.findings.map((f: any, i: number) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <p><strong>规则:</strong> {f.rule}</p>
                    <p><strong>风险:</strong> {f.risk}</p>
                    <p><strong>描述:</strong> {f.description}</p>
                    <p><strong>匹配次数:</strong> {f.match_count}</p>
                  </Card>
                ))}
              </div>
            )}
            {(!currentScan.findings || currentScan.findings.length === 0) && (
              <Typography.Paragraph style={{ marginTop: 16, color: '#52c41a' }}>✅ 未发现风险</Typography.Paragraph>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
