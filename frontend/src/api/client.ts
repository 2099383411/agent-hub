import axios from 'axios';

// 使用相对路径，nginx 会代理 /api/ 到后端
const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hub_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('hub_token');
      window.location.hash = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

export const authApi = {
  login: (password: string) => api.post('/auth/login', { password }),
};

export const dashboardApi = {
  overview: () => api.get('/dashboard/overview'),
};

export const agentApi = {
  list: () => api.get('/agents'),
  get: (id: string) => api.get(`/agents/${id}`),
  create: (data: any) => api.post('/agents', data),
  delete: (id: string) => api.delete(`/agents/${id}`),
  regenerate: (id: string) => api.post(`/agents/${id}/regenerate-credential`),
  refreshToken: (id: string) => api.post(`/agents/${id}/refresh-token`),
};

export const skillApi = {
  list: (params?: any) => api.get('/skills', { params }),
  get: (id: string) => api.get(`/skills/${id}`),
  upload: (file: File, scope = 'private', isMandatory = false) => {
    const form = new FormData();
    form.append('file', file);
    form.append('scope', scope);
    form.append('is_mandatory', String(isMandatory));
    return api.post('/skills/upload', form);
  },
  assign: (id: string, agentIds: string[]) => api.post(`/skills/${id}/assign`, { agent_ids: agentIds }),
  unassign: (id: string, agentIds: string[]) => api.post(`/skills/${id}/unassign`, { agent_ids: agentIds }),
  update: (id: string, data: any) => api.put(`/skills/${id}`, data),
  delete: (id: string) => api.delete(`/skills/${id}`),
  block: (id: string) => api.post(`/skills/${id}/block`),
};

export const securityApi = {
  listScans: (skillId?: string) => api.get('/security/scans', { params: { skill_id: skillId } }),
  getScan: (id: string) => api.get(`/security/scans/${id}`),
};

export const knowledgeApi = {
  list: (category?: string) => api.get('/knowledge', { params: { category } }),
  get: (id: string) => api.get(`/knowledge/${id}`),
  create: (data: any) => api.post('/knowledge', data),
  update: (id: string, data: any) => api.put(`/knowledge/${id}`, data),
  delete: (id: string) => api.delete(`/knowledge/${id}`),
};

export const complianceApi = {
  status: () => api.get('/compliance/status'),
  mandatory: () => api.get('/compliance/mandatory'),
};

export const systemApi = {
  health: () => api.get('/system/health'),
  getOnboarding: () => api.get('/system/onboarding'),
  updateOnboarding: (content: string) => api.put('/system/onboarding', { content }),
};

export const auditApi = {
  list: (params?: any) => api.get('/audit-logs', { params }),
  stats: () => api.get('/audit-logs/stats'),
};
