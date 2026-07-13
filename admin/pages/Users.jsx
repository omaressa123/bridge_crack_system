import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner, Modal } from '../components/AdminUI';

const ROLES = ['Admin', 'Bridge Engineer', 'Inspector', 'Viewer'];

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState({ full_name: '', email: '', role: 'Bridge Engineer' });

  const load = async () => {
    setLoading(true);
    try {
      setUsers(await adminApi.listUsers());
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createUser = async (e) => {
    e.preventDefault();
    try {
      await adminApi.createUser(form);
      setModal(null);
      setForm({ full_name: '', email: '', role: 'Bridge Engineer' });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'full_name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role', render: (u) => (
      <select
        value={u.role}
        onChange={async (e) => {
          await adminApi.updateUser(u.id, { role: e.target.value });
          load();
        }}
        className="admin-select-sm"
        aria-label={`Role for ${u.full_name}`}
      >
        {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
      </select>
    )},
    { key: 'google_id', label: 'Google ID', render: (u) => <code className="admin-code">{u.google_id?.slice(0, 16)}…</code> },
    { key: 'last_login', label: 'Last Login', render: (u) => u.last_login ? new Date(u.last_login).toLocaleString() : '—' },
    { key: 'is_active', label: 'Status', render: (u) => (
      <span className={`admin-pill ${u.is_active ? 'success' : 'danger'}`}>
        {u.is_active ? 'Active' : 'Disabled'}
      </span>
    )},
    { key: 'actions', label: 'Actions', render: (u) => (
      <div className="admin-actions">
        <button type="button" className="admin-btn admin-btn-sm" onClick={async () => { await adminApi.toggleUser(u.id); load(); }}>
          {u.is_active ? 'Disable' : 'Enable'}
        </button>
        <button type="button" className="admin-btn admin-btn-sm danger" onClick={async () => {
          if (confirm('Delete this user?')) { await adminApi.deleteUser(u.id); load(); }
        }}>Delete</button>
      </div>
    )},
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <div className="admin-toolbar">
        <button type="button" className="admin-btn primary" onClick={() => setModal('create')}>+ Create User</button>
      </div>
      <DataTable columns={columns} rows={users} emptyMessage="No users found" />
      {modal === 'create' && (
        <Modal title="Create User" onClose={() => setModal(null)}>
          <form onSubmit={createUser} className="admin-form">
            <label>Full Name<input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
            <label>Email<input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
            <label>Role
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </label>
            <div className="admin-form-actions">
              <button type="submit" className="admin-btn primary">Create</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
