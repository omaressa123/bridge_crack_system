import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { ErrorBanner, LoadingSpinner, StatCard } from '../components/AdminUI';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setStats(await adminApi.dashboardStats());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      {stats && (
        <>
          <div className="admin-stat-grid">
            <StatCard label="Users" value={stats.users} />
            <StatCard label="Bridges" value={stats.bridges} />
            <StatCard label="Cracks" value={stats.cracks} />
            <StatCard label="Pending Reviews" value={stats.pending_reviews} accent="warn" />
            <StatCard label="Models" value={stats.models} />
            <StatCard label="Production Model" value={stats.production_model} accent="success" />
          </div>
          <section className="admin-section">
            <h2>Dataset Overview</h2>
            <div className="admin-stat-grid">
              <StatCard label="Approved" value={stats.dataset.approved_images} accent="success" />
              <StatCard label="Rejected" value={stats.dataset.rejected_images} />
              <StatCard label="Pending" value={stats.dataset.pending_images} accent="warn" />
              <StatCard label="Training Set" value={stats.dataset.training_images} />
              <StatCard label="Validation" value={stats.dataset.validation_images} />
              <StatCard label="Test" value={stats.dataset.test_images} />
            </div>
            {stats.dataset.ready_for_retrain && (
              <div className="admin-alert success">
                New training data available — {stats.dataset.approved_images} approved images (threshold: {stats.dataset.retrain_threshold})
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
