import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner } from '../components/AdminUI';

export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      setModels(await adminApi.listModels());
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const columns = [
    { key: 'version', label: 'Version' },
    { key: 'status', label: 'Status', render: (m) => (
      <span className={`admin-pill ${m.status === 'production' ? 'success' : m.status}`}>{m.status}</span>
    )},
    { key: 'map50', label: 'mAP50', render: (m) => m.map50?.toFixed(3) ?? '—' },
    { key: 'map50_95', label: 'mAP50-95', render: (m) => m.map50_95?.toFixed(3) ?? '—' },
    { key: 'precision_score', label: 'Precision', render: (m) => m.precision_score?.toFixed(3) ?? '—' },
    { key: 'recall_score', label: 'Recall', render: (m) => m.recall_score?.toFixed(3) ?? '—' },
    { key: 'epochs', label: 'Epochs' },
    { key: 'training_images', label: 'Train Imgs' },
    { key: 'trained_at', label: 'Date', render: (m) => new Date(m.trained_at).toLocaleString() },
    { key: 'actions', label: 'Actions', render: (m) => (
      <div className="admin-actions">
        {m.status !== 'production' && (
          <button type="button" className="admin-btn admin-btn-sm primary" onClick={async () => {
            if (confirm(`Deploy ${m.version} to production?`)) {
              await adminApi.deployModel(m.id);
              load();
            }
          }}>Deploy</button>
        )}
        {m.status === 'production' && (
          <button type="button" className="admin-btn admin-btn-sm" onClick={async () => {
            const prev = models.find((x) => x.status === 'archived');
            if (prev && confirm(`Rollback to ${prev.version}?`)) {
              await adminApi.rollbackModel(prev.id);
              load();
            }
          }}>Rollback</button>
        )}
      </div>
    )},
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <p className="admin-muted">Only one model can be in production. Deployment requires admin approval.</p>
      <DataTable columns={columns} rows={models} emptyMessage="No trained models yet. Start retraining from the Dataset page." />
    </div>
  );
}
