import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import { adminApi } from './api/adminApi';
import DashboardPage from './pages/Dashboard';
import UsersPage from './pages/Users';
import BridgesPage from './pages/Bridges';
import CracksPage from './pages/Cracks';
import ImageReviewPage from './pages/ImageReview';
import DatasetPage from './pages/Dataset';
import ModelsPage from './pages/Models';
import SensorsPage from './pages/Sensors';
import ReportsPage from './pages/Reports';
import NotificationsPage from './pages/Notifications';
import AuditLogPage from './pages/AuditLog';
import { ErrorBanner, LoadingSpinner } from './components/AdminUI';
import './Admin.css';

const PAGES = {
  dashboard: DashboardPage,
  users: UsersPage,
  bridges: BridgesPage,
  cracks: CracksPage,
  'image-review': ImageReviewPage,
  dataset: DatasetPage,
  models: ModelsPage,
  sensors: SensorsPage,
  reports: ReportsPage,
  notifications: NotificationsPage,
  audit: AuditLogPage,
};

export default function AdminApp({ user, onExit }) {
  const [page, setPage] = useState('dashboard');
  const [authorized, setAuthorized] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.role !== 'Admin' && user?.role !== 'ADMIN') {
      setAuthorized(false);
      return;
    }
    adminApi.dashboardStats()
      .then(() => setAuthorized(true))
      .catch((e) => {
        setAuthorized(false);
        setError(e.message);
      });
  }, [user]);

  useEffect(() => {
    if (!authorized) return;
    const poll = () => adminApi.listNotifications().then((n) => {
      setUnreadCount(n.filter((x) => !x.is_read).length);
    }).catch(() => {});
    poll();
    const t = setInterval(poll, 30000);
    return () => clearInterval(t);
  }, [authorized]);

  if (authorized === null) return <LoadingSpinner label="Verifying admin access…" />;
  if (!authorized) {
    return (
      <div className="admin-denied">
        <h2>Access Denied</h2>
        <p>Only Admin users can access the control panel.</p>
        <ErrorBanner message={error} />
        <button type="button" className="admin-btn" onClick={onExit}>← Back</button>
      </div>
    );
  }

  const Page = PAGES[page] || DashboardPage;
  return (
    <AdminLayout page={page} setPage={setPage} user={user} onExit={onExit} unreadCount={unreadCount}>
      <Page />
    </AdminLayout>
  );
}
