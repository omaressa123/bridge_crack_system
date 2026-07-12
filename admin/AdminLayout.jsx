import React from 'react';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'users', label: 'Users', icon: '👥' },
  { id: 'bridges', label: 'Bridges', icon: '🌉' },
  { id: 'cracks', label: 'Cracks', icon: '🔍' },
  { id: 'image-review', label: 'Image Review', icon: '🖼️' },
  { id: 'dataset', label: 'Dataset', icon: '📦' },
  { id: 'models', label: 'Models', icon: '🤖' },
  { id: 'sensors', label: 'Sensors', icon: '📡' },
  { id: 'reports', label: 'Reports', icon: '📄' },
  { id: 'notifications', label: 'Notifications', icon: '🔔' },
  { id: 'audit', label: 'Audit Log', icon: '📋' },
];

export default function AdminLayout({ page, setPage, user, onExit, children, unreadCount }) {
  return (
    <div className="admin-app">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <span>Bridge Admin</span>
          <small>Control Panel</small>
        </div>
        <nav className="admin-nav" aria-label="Admin navigation">
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`admin-nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => setPage(item.id)}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
              {item.id === 'notifications' && unreadCount > 0 && (
                <span className="admin-badge">{unreadCount}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <div className="admin-user-chip">
            {user?.picture && <img src={user.picture} alt="" />}
            <div>
              <strong>{user?.name}</strong>
              <small>{user?.role}</small>
            </div>
          </div>
          <button type="button" className="admin-btn admin-btn-ghost" onClick={onExit}>
            ← Back to App
          </button>
        </div>
      </aside>
      <main className="admin-main">
        <header className="admin-topbar">
          <h1>{NAV.find((n) => n.id === page)?.label || 'Admin'}</h1>
        </header>
        <div className="admin-content">{children}</div>
      </main>
    </div>
  );
}

export { NAV };
