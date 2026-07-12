import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner } from '../components/AdminUI';

export default function CracksPage() {
  const [cracks, setCracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [selected, setSelected] = useState([]);

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (status) params.status = status;
      setCracks(await adminApi.listCracks(params));
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const toggleSelect = (id) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const columns = [
    { key: 'sel', label: '', render: (c) => (
      <input type="checkbox" checked={selected.includes(c.id)} onChange={() => toggleSelect(c.id)} aria-label={`Select crack ${c.id}`} />
    )},
    { key: 'id', label: 'ID' },
    { key: 'bridge_name', label: 'Bridge' },
    { key: 'severity_level', label: 'Severity', render: (c) => (
      <span className={`admin-pill sev-${c.severity_level}`}>L{c.severity_level}</span>
    )},
    { key: 'confidence', label: 'Conf.', render: (c) => `${(c.confidence * 100).toFixed(0)}%` },
    { key: 'area', label: 'Area', render: (c) => c.area?.toFixed(0) },
    { key: 'status', label: 'Status', render: (c) => <span className={`admin-pill ${c.status}`}>{c.status}</span> },
    { key: 'detected_at', label: 'Detected', render: (c) => new Date(c.detected_at).toLocaleDateString() },
    { key: 'actions', label: 'Actions', render: (c) => (
      <div className="admin-actions">
        <button type="button" className="admin-btn admin-btn-sm success" onClick={async () => { await adminApi.approveCrack(c.id); load(); }}>Approve</button>
        <button type="button" className="admin-btn admin-btn-sm" onClick={async () => { await adminApi.rejectCrack(c.id); load(); }}>Reject</button>
        <button type="button" className="admin-btn admin-btn-sm danger" onClick={async () => {
          if (confirm('Delete crack?')) { await adminApi.deleteCrack(c.id); load(); }
        }}>Delete</button>
      </div>
    )},
  ];

  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <div className="admin-toolbar">
        <input className="admin-search" placeholder="Search cracks…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search cracks" />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="admin-select" aria-label="Filter by status">
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="merged">Merged</option>
        </select>
        <button type="button" className="admin-btn" onClick={load}>Filter</button>
        {selected.length >= 2 && (
          <button type="button" className="admin-btn primary" onClick={async () => {
            await adminApi.mergeCracks({ crack_ids: selected });
            setSelected([]);
            load();
          }}>Merge Selected ({selected.length})</button>
        )}
      </div>
      {loading ? <LoadingSpinner /> : <DataTable columns={columns} rows={cracks} />}
    </div>
  );
}
