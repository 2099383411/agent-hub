import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Space, message, Typography, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { knowledgeApi } from '../api/client';

export default function Knowledge() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [current, setCurrent] = useState<any>(null);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res: any = await knowledgeApi.list();
      setEntries(res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onSave = async (values: any) => {
    if (current) {
      await knowledgeApi.update(current.id, values);
      message.success('已更新');
    } else {
      await knowledgeApi.create(values);
      message.success('已创建');
    }
    setEditOpen(false);
    form.resetFields();
    setCurrent(null);
    load();
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '分类', dataIndex: 'category', key: 'category' },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    {
      title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => {
            setCurrent(record);
            form.setFieldsValue(record);
            setEditOpen(true);
          }}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => knowledgeApi.delete(record.id).then(load)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>知识库</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setCurrent(null); form.resetFields(); setEditOpen(true); }}>新增</Button>
      </div>

      <Table dataSource={entries} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal title={current ? '编辑知识' : '新增知识'} open={editOpen} onOk={() => form.submit()} onCancel={() => { setEditOpen(false); form.resetFields(); setCurrent(null); }} width={720}>
        <Form form={form} layout="vertical" onFinish={onSave}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="category" label="分类">
            <Input placeholder="如：deployment, guide, faq" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <Input.TextArea rows={12} placeholder="支持 Markdown 格式" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
