import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

export default function Dashboard({ language, t, bridgeId }) {
  const [bridgeData, setBridgeData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!bridgeId) return;
    
    const fetchBridgeStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/bridge/${bridgeId}/status`);
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
          setBridgeData(null);
        } else {
          setError(null);
          setBridgeData({
            bridge_name: data.bridge_name,
            city: data.city,
            overall_severity: data.overall_severity,
            total_cracks: data.total_cracks,
            high_severity_cracks: data.high_severity_cracks,
            last_inspection: data.last_inspection_date,
            recommendation: data.recommendation,
            sensors: data.current_sensors,
          });
        }
        
      } catch (error) {
        console.error('Failed to fetch bridge status:', error);
        setError('Failed to load bridge data');
      }
    };
    
    fetchBridgeStatus();
    const interval = setInterval(fetchBridgeStatus, 300000); // Every 5 minutes
    
    return () => clearInterval(interval);
  }, [bridgeId]);

  const translations = {
    en: {
      overallStatus: 'Overall Status',
      bridgeInfo: 'Bridge Information',
      cracks: 'Cracks Detected',
      highSeverity: 'High Severity',
      lastInspection: 'Last Inspection',
      recommendation: 'Recommendation',
      safe: 'Safe',
      monitor: 'Monitor',
      urgent: 'Urgent Repair',
      temperature: 'Temperature (°C)',
      moisture: 'Moisture (%)',
      vibration: 'Vibration (g)',
      strain: 'Strain (μ)',
      recentActivity: 'Recent Activity',
      noActivity: 'No recent activity',
    },
    ar: {
      overallStatus: 'الحالة العامة',
      bridgeInfo: 'معلومات الجسر',
      cracks: 'الشروخ المكتشفة',
      highSeverity: 'شدة عالية',
      lastInspection: 'آخر فحص',
      recommendation: 'التوصية',
      safe: 'آمن',
      monitor: 'راقب بانتظام',
      urgent: 'إصلاح عاجل',
      temperature: 'درجة الحرارة (°C)',
      moisture: 'الرطوبة (%)',
      vibration: 'الاهتزاز (g)',
      strain: 'الإجهاد (μ)',
      recentActivity: 'النشاط الأخير',
      noActivity: 'لا توجد أنشطة حديثة',
    }
  };

  const trans = translations[language];

  const severityLevels = {
    1: { name: trans.safe, color: '#10b981', emoji: '✅' },
    2: { name: trans.monitor, color: '#f59e0b', emoji: '⚠️' },
    3: { name: trans.urgent, color: '#ef4444', emoji: '🚨' },
  };

  if (!bridgeId) {
    return <div className="dashboard"><div className="card"><p>Please select a bridge</p></div></div>;
  }

  if (error) {
    return <div className="dashboard"><div className="card"><p className="error-message">Error: {error}</p></div></div>;
  }

  if (!bridgeData) {
    return <div className="dashboard"><div className="card"><p>Loading...</p></div></div>;
  }

  const severity = severityLevels[bridgeData.overall_severity];

  return (
    <div className="dashboard">
      <div className="card severity-card">
        <div className="card-header">{trans.overallStatus}</div>
        <div className="severity-display">
          <div className="severity-emoji">{severity.emoji}</div>
          <div className="severity-info">
            <h2 style={{ color: severity.color }}>{severity.name}</h2>
            <p>Bridge ID: {bridgeId}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">{trans.bridgeInfo}</div>
        <div className="info-grid">
          <div className="info-item">
            <label>Bridge Name</label>
            <p>{bridgeData.bridge_name}</p>
          </div>
          <div className="info-item">
            <label>City</label>
            <p>{bridgeData.city}</p>
          </div>
          <div className="info-item">
            <label>{trans.lastInspection}</label>
            <p>{bridgeData.last_inspection}</p>
          </div>
          <div className="info-item">
            <label>{trans.recommendation}</label>
            <p>{bridgeData.recommendation}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">{trans.cracks}</div>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-number">{bridgeData.total_cracks}</div>
            <div className="stat-label">{trans.cracks}</div>
          </div>
          <div className="stat-box highlight">
            <div className="stat-number">{bridgeData.high_severity_cracks}</div>
            <div className="stat-label">{trans.highSeverity}</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Live Sensor Data</div>
        <div className="sensor-grid">
          <div className="sensor-box">
            <div className="sensor-value">{bridgeData.sensors.temperature}°</div>
            <div className="sensor-label">{trans.temperature}</div>
            <div className="sensor-bar" style={{ width: `${(bridgeData.sensors.temperature / 50) * 100}%` }}></div>
          </div>
          <div className="sensor-box">
            <div className="sensor-value">{bridgeData.sensors.moisture}%</div>
            <div className="sensor-label">{trans.moisture}</div>
            <div className="sensor-bar" style={{ width: `${bridgeData.sensors.moisture}%` }}></div>
          </div>
          <div className="sensor-box">
            <div className="sensor-value">{bridgeData.sensors.vibration}g</div>
            <div className="sensor-label">{trans.vibration}</div>
            <div className="sensor-bar" style={{ width: `${(bridgeData.sensors.vibration / 2) * 100}%` }}></div>
          </div>
          <div className="sensor-box">
            <div className="sensor-value">{bridgeData.sensors.strain}μ</div>
            <div className="sensor-label">{trans.strain}</div>
            <div className="sensor-bar" style={{ width: `${(bridgeData.sensors.strain / 200) * 100}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
