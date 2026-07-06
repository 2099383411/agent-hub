import { useState } from 'react';
import { Card, Input, Button, Table, Tag, Space, message, Typography, Modal, Select } from 'antd';
import { SearchOutlined, ImportOutlined } from '@ant-design/icons';
import {  } from '../api/client';
import axios from 'axios';

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8200/api/v1`;

export default function Market() {
  const [query, setQuery] = useState('');
  const [source, setSource] = useState<string>('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [importOpen, setImportOpen] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('hub_token');
      const params: any = { q: query.trim() };
      if (source) params.source = source;
      const res = await axios.get(`${API_BASE}/public-hub/search`, {
        params, headers: { Authorization: `Bearer ${token}` },
      });
      setResults(res.data?.data?.results || []);
      if (res.data?.data?.results?.length === 0) {
        message.info('未找到匹配的技能');
      }
    } catch (err: any) {
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const doImport = async (name: string, src: string, sourceUrl?: string) => {
    setImporting(true);
    try {
      const token = localStorage.getItem('hub_token');
      const res = await axios.post(`${API_BASE}/public-hub/import`,
        { name, source: src, source_url: sourceUrl },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } },
      );
      setImportResult(res.data?.data);
      setImportOpen(true);
      message.success('技能导入成功，已完成安全检测');
    } catch (err: any) {
      message.error(err.response?.data?.detail || '导入失败');
    } finally {
      setImporting(false);
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'display_name', key: 'display_name' },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '分类', dataIndex: 'category', key: 'category' },
    {
      title: '来源', dataIndex: 'source', key: 'source',
      render: (s: string) => <Tag>{s === 'clawhub' ? '🐾 ClawHub' : '📦 SkillHub'}</Tag>,
    },
    { title: '下载量', dataIndex: 'download_count', key: 'download_count' },
    {
      title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Button
          type="primary"
          size="small"
          icon={<ImportOutlined />}
          loading={importing}
          onClick={() => doImport(record.name, record.source, record.source_url)}
        >
          导入
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>公共市场</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input.Search
            placeholder="搜索 ClawHub / SkillHub 技能..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={search}
            enterButton={<><SearchOutlined /> 搜索</>}
            style={{ flex: 1 }}
          />
          <Select
            value={source}
            onChange={setSource}
            style={{ width: 140 }}
            options={[
              { value: '', label: '全部来源' },
              { value: 'clawhub', label: '🐾 ClawHub' },
              { value: 'skillhub', label: '📦 SkillHub' },
            ]}
          />
        </Space.Compact>
      </Card>

      <Table
        dataSource={results}
        columns={columns}
        rowKey={(r) => `${r.name}|${r.source}`}
        loading={loading}
        size="small"
        locale={{ emptyText: '在上方搜索公共平台的技能' }}
      />

      <Modal
        title="导入结果"
        open={importOpen}
        onCancel={() => setImportOpen(false)}
        footer={[
          <Button key="close" onClick={() => setImportOpen(false)}>关闭</Button>,
          <Button key="goto" type="primary" onClick={() => { setImportOpen(false); window.location.hash = '/skills'; }}>
            前往技能库查看
          </Button>,
        ]}
      >
        {importResult && (
          <div>
            <p><strong>名称：</strong>{importResult.name}</p>
            <p><strong>版本：</strong>{importResult.version}</p>
            <p><strong>来源：</strong>{importResult.source}</p>
            <p><strong>安全状态：</strong>
              <Tag color={importResult.security_status === 'passed' ? 'green' : importResult.security_status === 'warning' ? 'orange' : 'red'}>
                {importResult.security_status === 'passed' ? '✅ 通过' : importResult.security_status === 'warning' ? '⚠️ 有风险' : '❌ 高危'}
              </Tag>
            </p>
          </div>
        )}
      </Modal>
    </div>
  );
}
