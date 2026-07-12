import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner } from '../components/AdminUI';

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      setLogs(await adminApi.auditLog(200));
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const columns = [
    { key: 'timestamp', label: 'When', render: (l) => new Date(l.timestamp).toLocaleString() },
    { key: 'user_name', label: 'Who' },
    { key: 'action', label: 'What' },
    { key: 'entity_type', label: 'Entity' },
    { key: 'entity_id', label: 'ID' },
    { key: 'ip_address', label: 'IP' },
    { key: 'before_value', label: 'Before', render: (l) => <code className="admin-code">{l.before_value?.slice(0, 40)}</code> },
    { key: 'after_value', label: 'After', render: (l) => <code className="admin-code">{l.after_value?.slice(0, 40)}</code> },
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <DataTable columns={columns} rows={logs} emptyMessage="No audit entries yet" />
    </div>
  );
}
