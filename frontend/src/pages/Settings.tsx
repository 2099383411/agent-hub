import { useState, useEffect } from 'react';
import { Card, Form, Input, Button, message, Typography, Spin, Descriptions } from 'antd';
import { systemApi } from '../api/client';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [onboarding, setOnboarding] = useState<any>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    systemApi.getOnboarding().then((res: any) => {
      setOnboarding(res.data);
      form.setFieldsValue({ content: res.data?.content || '' });
    }).finally(() => setLoading(false));
  }, []);

  const onSave = async (values: { content: string }) => {
    setSaving(true);
    try {
      const res: any = await systemApi.updateOnboarding(values.content);
      message.success(`入职规范已更新 (v${res.data?.version})`);
      setOnboarding({ ...onboarding, version: res.data?.version, content: values.content });
    } catch {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <Typography.Title level={4}>系统设置</Typography.Title>

      <Card title="中台使用规范 (Onboarding)" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="当前版本">{onboarding?.version || 1}</Descriptions.Item>
          <Descriptions.Item label="最后更新">{onboarding?.updated_at || '-'}</Descriptions.Item>
        </Descriptions>

        <Typography.Paragraph type="secondary">
          Agent 接入中台时调 <code>hub.onboarding()</code> 获取此规范并写入自身记忆。
          修改后版本号自动递增，Agent 下次调用时会发现更新并重新学习。
        </Typography.Paragraph>

        <Form form={form} layout="vertical" onFinish={onSave}>
          <Form.Item name="content" label="规范内容（Markdown）" rules={[{ required: true, message: '请输入规范内容' }]}>
            <Input.TextArea rows={16} placeholder="# Agent Hub 工作规范&#10;&#10;## 你是谁&#10;" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={saving}>保存并递增版本</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
