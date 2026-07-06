import { useState } from 'react';
import { Card, Form, Input, Button, message, Typography, Space } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { password: string }) => {
    setLoading(true);
    try {
      const res: any = await authApi.login(values.password);
      // 登录接口返回 LoginResponse { token, token_type, expires_in }
      // axios 拦截器已解一层，res 即为响应体
      localStorage.setItem('hub_token', res.token);
      message.success('登录成功');
      navigate('/');
    } catch (err: any) {
      message.error(err.response?.data?.detail || '登录失败，请检查密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f5f5f5' }}>
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Space direction="vertical" style={{ width: '100%', textAlign: 'center', marginBottom: 24 }}>
          <Typography.Title level={3}>Agent Hub</Typography.Title>
          <Typography.Text type="secondary">智能体中台管理系统</Typography.Text>
        </Space>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="password" rules={[{ required: true, message: '请输入管理员密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="管理员密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
