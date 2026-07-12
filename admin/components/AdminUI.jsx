import React from 'react';

export function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className="admin-loading" role="status" aria-live="polite">
      <div className="admin-spinner" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="admin-error" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button type="button" className="admin-btn admin-btn-sm" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function StatCard({ label, value, accent }) {
  return (
    <div className={`admin-stat-card ${accent || ''}`}>
      <div className="admin-stat-value">{value}</div>
      <div className="admin-stat-label">{label}</div>
    </div>
  );
}

export function Modal({ title, children, onClose, wide }) {
  return (
    <div className="admin-modal-overlay" onClick={onClose} role="presentation">
      <div
        className={`admin-modal ${wide ? 'admin-modal-wide' : ''}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="admin-modal-header">
          <h3>{title}</h3>
          <button type="button" className="admin-modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="admin-modal-body">{children}</div>
      </div>
    </div>
  );
}

export function DataTable({ columns, rows, emptyMessage = 'No data' }) {
  if (!rows?.length) {
    return <p className="admin-empty">{emptyMessage}</p>;
  }
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key || col.label}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id ?? i}>
              {columns.map((col) => (
                <td key={col.key || col.label}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
