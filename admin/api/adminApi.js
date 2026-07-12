import { authenticatedFetch, API_URL } from '../../api';

const ADMIN_BASE = `${API_URL}/admin`;

async function request(path, options = {}) {
  const res = await authenticatedFetch(`${ADMIN_BASE}${path}`, options);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || data.detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res;
}

export const adminApi = {
  dashboardStats: () => request('/dashboard/stats'),

  // Users
  listUsers: () => request('/users'),
  createUser: (data) => request('/users', { method: 'POST', body: JSON.stringify(data) }),
  updateUser: (id, data) => request(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteUser: (id) => request(`/users/${id}`, { method: 'DELETE' }),
  toggleUser: (id) => request(`/users/${id}/toggle-active`, { method: 'POST' }),

  // Bridges
  listBridges: () => request('/bridges'),
  createBridge: (data) => request('/bridges', { method: 'POST', body: JSON.stringify(data) }),
  updateBridge: (id, data) => request(`/bridges/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteBridge: (id) => request(`/bridges/${id}`, { method: 'DELETE' }),
  uploadBridgeImage: (id, file) => {
    const fd = new FormData();
    fd.append('image', file);
    return request(`/bridges/${id}/image`, { method: 'POST', body: fd });
  },

  // Cracks
  listCracks: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/cracks${qs ? `?${qs}` : ''}`);
  },
  updateCrack: (id, data) => request(`/cracks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  approveCrack: (id) => request(`/cracks/${id}/approve`, { method: 'POST' }),
  rejectCrack: (id) => request(`/cracks/${id}/reject`, { method: 'POST' }),
  mergeCracks: (data) => request('/cracks/merge', { method: 'POST', body: JSON.stringify(data) }),
  deleteCrack: (id) => request(`/cracks/${id}`, { method: 'DELETE' }),

  // Image reviews
  listImageReviews: (status) => request(`/image-reviews${status ? `?status=${status}` : ''}`),
  uploadForReview: (file, bridgeId, camera) => {
    const fd = new FormData();
    fd.append('image', file);
    const params = new URLSearchParams();
    if (bridgeId) params.set('bridge_id', bridgeId);
    if (camera) params.set('camera', camera);
    const qs = params.toString();
    return request(`/image-reviews/upload${qs ? `?${qs}` : ''}`, { method: 'POST', body: fd });
  },
  decideReview: (id, data) => request(`/image-reviews/${id}/decide`, { method: 'POST', body: JSON.stringify(data) }),
  updateReview: (id, data) => request(`/image-reviews/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  reviewImageUrl: (id) => `${ADMIN_BASE}/image-reviews/${id}/image`,

  // Dataset
  datasetStats: () => request('/dataset/stats'),
  datasetImages: () => request('/dataset/images'),
  setRetrainThreshold: (threshold) => request('/dataset/threshold', { method: 'PUT', body: JSON.stringify({ threshold }) }),
  startRetraining: () => request('/retraining/start', { method: 'POST' }),
  listTrainingJobs: () => request('/retraining/jobs'),

  // Models
  listModels: () => request('/models'),
  deployModel: (id) => request(`/models/${id}/deploy`, { method: 'POST' }),
  rollbackModel: (id) => request(`/models/${id}/rollback`, { method: 'POST' }),

  // Sensors
  listSensors: () => request('/sensors'),
  reconnectSensors: () => request('/sensors/reconnect', { method: 'POST' }),

  // Reports
  downloadInspectionPdf: () => `${ADMIN_BASE}/reports/inspection/pdf`,
  downloadMaintenanceExcel: () => `${ADMIN_BASE}/reports/maintenance/excel`,

  // Notifications
  listNotifications: () => request('/notifications'),
  markNotificationRead: (id) => request(`/notifications/${id}/read`, { method: 'POST' }),
  sendNotification: (data) => request('/notifications/send', { method: 'POST', body: JSON.stringify(data) }),

  // Audit
  auditLog: (limit = 100) => request(`/audit-log?limit=${limit}`),
};
