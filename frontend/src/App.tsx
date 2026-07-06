import { useState } from "react";
import { Button, ConfigProvider, Layout, Menu } from 'antd';
import {
  DashboardOutlined, RobotOutlined, AppstoreOutlined,
  SafetyCertificateOutlined, BookOutlined, CheckCircleOutlined,
  LoginOutlined, GlobalOutlined, AuditOutlined,
} from '@ant-design/icons';
import { RouterProvider, createHashRouter, Navigate, useNavigate, useLocation, Outlet } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import AgentList from './pages/AgentList';
import SkillList from './pages/SkillList';
import Login from './pages/Login';
import Knowledge from './pages/Knowledge';
import Compliance from './pages/Compliance';
import Security from './pages/Security';
import Market from './pages/Market';
import AuditLog from './pages/AuditLog';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/agents', icon: <RobotOutlined />, label: 'Agent' },
  { key: '/skills', icon: <AppstoreOutlined />, label: '技能库' },
  { key: '/market', icon: <GlobalOutlined />, label: '公共市场' },
  { key: '/security', icon: <SafetyCertificateOutlined />, label: '安检' },
  { key: '/compliance', icon: <CheckCircleOutlined />, label: '合规' },
  { key: '/audit', icon: <AuditOutlined />, label: '审计' },
  { key: '/knowledge', icon: <BookOutlined />, label: '知识库' },
];

function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const token = localStorage.getItem('hub_token');
  if (!token) return <Navigate to="/login" />;
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ height: 48, margin: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', fontSize: collapsed ? 14 : 18 }}>
          {collapsed ? 'AH' : 'Agent Hub'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <Button type="text" icon={<LoginOutlined />} onClick={() => { localStorage.removeItem('hub_token'); navigate('/login'); }}>退出</Button>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

const router = createHashRouter([
  { path: '/login', element: <Login /> },
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'agents', element: <AgentList /> },
      { path: 'skills', element: <SkillList /> },
      { path: 'market', element: <Market /> },
      { path: 'security', element: <Security /> },
      { path: 'compliance', element: <Compliance /> },
      { path: 'audit', element: <AuditLog /> },
      { path: 'knowledge', element: <Knowledge /> },
    ],
  },
]);

export default function App() {
  return (
    <ConfigProvider theme={{ token: { colorPrimary: '#1677ff', borderRadius: 6 } }}>
      <RouterProvider router={router} />
    </ConfigProvider>
  );
}
