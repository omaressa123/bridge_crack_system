import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner, StatCard } from '../components/AdminUI';

export default function DatasetPage() {
  const [stats, setStats] = useState(null);
  const [images, setImages] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [threshold, setThreshold] = useState(100);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [training, setTraining] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [s, imgs, j] = await Promise.all([
        adminApi.datasetStats(),
        adminApi.datasetImages(),
        adminApi.listTrainingJobs(),
      ]);
      setStats(s);
      setThreshold(s.retrain_threshold);
      setImages(imgs);
      setJobs(j);
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, []);

  const startTrain = async () => {
    setTraining(true);
    try {
      await adminApi.startRetraining();
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setTraining(false);
    }
  };

  const saveThreshold = async () => {
    await adminApi.setRetrainThreshold(Number(threshold));
    load();
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'review_status', label: 'Review', render: (r) => <span className={`admin-pill ${r.review_status}`}>{r.review_status}</span> },
    { key: 'approved_label', label: 'Label' },
    { key: 'training_status', label: 'Training' },
    { key: 'confidence', label: 'Conf.', render: (r) => r.confidence ? `${(r.confidence * 100).toFixed(0)}%` : '—' },
    { key: 'bridge_id', label: 'Bridge' },
    { key: 'review_time', label: 'Reviewed', render: (r) => r.review_time ? new Date(r.review_time).toLocaleString() : '—' },
  ];

  const jobColumns = [
    { key: 'id', label: 'Job' },
    { key: 'status', label: 'Status', render: (j) => <span className={`admin-pill ${j.status}`}>{j.status}</span> },
    { key: 'progress', label: 'Progress', render: (j) => `${j.progress}%` },
    { key: 'created_at', label: 'Started', render: (j) => new Date(j.created_at).toLocaleString() },
  ];

  if (loading && !stats) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      {stats && (
        <div className="admin-stat-grid">
          <StatCard label="Approved" value={stats.approved_images} accent="success" />
          <StatCard label="Rejected" value={stats.rejected_images} />
          <StatCard label="Pending" value={stats.pending_images} accent="warn" />
          <StatCard label="Training" value={stats.training_images} />
          <StatCard label="Validation" value={stats.validation_images} />
          <StatCard label="Test" value={stats.test_images} />
        </div>
      )}
      <section className="admin-section">
        <h2>Retraining Queue</h2>
        <div className="admin-toolbar">
          <label>Threshold:
            <input type="number" min={1} value={threshold} onChange={(e) => setThreshold(e.target.value)} className="admin-input-sm" />
          </label>
          <button type="button" className="admin-btn" onClick={saveThreshold}>Save</button>
          {stats?.ready_for_retrain && (
            <div className="admin-alert success">New training data available.</div>
          )}
          <button type="button" className="admin-btn primary" disabled={!stats?.ready_for_retrain || training} onClick={startTrain}>
            {training ? 'Starting…' : 'Retrain Model'}
          </button>
        </div>
        <DataTable columns={jobColumns} rows={jobs} emptyMessage="No training jobs yet" />
      </section>
      <section className="admin-section">
        <h2>All Reviewed Images</h2>
        <DataTable columns={columns} rows={images} />
      </section>
    </div>
  );
}
