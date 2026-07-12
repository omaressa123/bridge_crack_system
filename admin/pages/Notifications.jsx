import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner } from '../components/AdminUI';

export default function NotificationsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ title: '', message: '', notification_type: 'alert', send_email: false, bridge_name: '' });

  const load = async () => {
    setLoading(true);
    try {
      setItems(await adminApi.listNotifications());
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const send = async (e) => {
    e.preventDefault();
    try {
      await adminApi.sendNotification(form);
      setForm({ title: '', message: '', notification_type: 'alert', send_email: false, bridge_name: '' });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { key: 'title', label: 'Title' },
    { key: 'message', label: 'Message' },
    { key: 'notification_type', label: 'Type' },
    { key: 'is_read', label: 'Read', render: (n) => n.is_read ? '✓' : '—' },
    { key: 'created_at', label: 'Time', render: (n) => new Date(n.created_at).toLocaleString() },
    { key: 'actions', label: '', render: (n) => !n.is_read && (
      <button type="button" className="admin-btn admin-btn-sm" onClick={async () => { await adminApi.markNotificationRead(n.id); load(); }}>Mark read</button>
    )},
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <form onSubmit={send} className="admin-form admin-form-inline">
        <label>Title<input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
        <label>Message<input required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} /></label>
        <label>Bridge (for email)<input value={form.bridge_name} onChange={(e) => setForm({ ...form, bridge_name: e.target.value })} /></label>
        <label><input type="checkbox" checked={form.send_email} onChange={(e) => setForm({ ...form, send_email: e.target.checked })} /> Send email</label>
        <button type="submit" className="admin-btn primary">Send Alert</button>
      </form>
      <DataTable columns={columns} rows={items} />
    </div>
  );
}
