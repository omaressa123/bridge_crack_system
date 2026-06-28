import React from 'react';

export default function Navigation({ currentTab, setCurrentTab, language, t }) {
  const tabs = [
    { id: 'dashboard', label: t.dashboard, icon: '📊' },
    { id: 'cracks', label: t.cracks, icon: '🔍' },
    { id: 'sensors', label: t.sensors, icon: '📡' },
    { id: 'report', label: t.report, icon: '📋' },
  ];

  return (
    <nav className={`bottom-nav ${language === 'ar' ? 'rtl' : 'ltr'}`}>
      <div className="nav-container">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-btn ${currentTab === tab.id ? 'active' : ''}`}
            onClick={() => setCurrentTab(tab.id)}
          >
            <span className="nav-icon">{tab.icon}</span>
            <span className="nav-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
