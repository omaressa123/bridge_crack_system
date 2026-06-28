import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

export default function SensorMonitor({ language, t, bridgeId }) {
  const [sensorData, setSensorData] = useState(null);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('24h'); // 1h, 6h, 24h, 7d
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    if (!bridgeId) return;
    
    const fetchSensorData = async () => {
      try {
        const response = await fetch(
          `${API_URL}/sensors/data?bridge_id=${bridgeId}&limit=7`
        );
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
          setSensorData(null);
        } else {
          setError(null);
          setSensorData({
            temperature: data.temperature_history,
            moisture: data.moisture_history,
            vibration: data.vibration_history,
            strain: data.strain_history,
          });
        }
        
      } catch (error) {
        console.error('Failed to fetch sensor data:', error);
        setError('Failed to load sensor data');
      }
    };
    
    fetchSensorData();
    const interval = setInterval(fetchSensorData, 60000); // Every minute
    
    return () => clearInterval(interval);
  }, [bridgeId, timeRange]);

  const translations = {
    en: {
      sensors: 'Sensor Monitoring',
      temperature: 'Temperature (°C)',
      moisture: 'Moisture (%)',
      vibration: 'Vibration (g)',
      strain: 'Strain (μ)',
      alerts: 'Alerts & Anomalies',
      timeRange: 'Time Range',
      lastHour: 'Last Hour',
      lastDay: 'Last 24h',
      lastWeek: 'Last Week',
      anomaly: 'Anomaly Detected',
      highMoisture: 'High Moisture',
      highVibration: 'High Vibration',
      highStrain: 'High Strain',
      normal: 'Normal',
      noAlerts: 'No recent alerts',
      current: 'Current',
      avg: 'Average',
      max: 'Maximum',
      min: 'Minimum',
    },
    ar: {
      sensors: 'مراقبة المستشعرات',
      temperature: 'درجة الحرارة (°C)',
      moisture: 'الرطوبة (%)',
      vibration: 'الاهتزاز (g)',
      strain: 'الإجهاد (μ)',
      alerts: 'التنبيهات والحالات الشاذة',
      timeRange: 'نطاق الوقت',
      lastHour: 'الساعة الأخيرة',
      lastDay: 'آخر 24 ساعة',
      lastWeek: 'آخر أسبوع',
      anomaly: 'كشف حالة شاذة',
      highMoisture: 'رطوبة عالية',
      highVibration: 'اهتزاز عالي',
      highStrain: 'إجهاد عالي',
      normal: 'طبيعي',
      noAlerts: 'لا توجد تنبيهات حديثة',
      current: 'الحالي',
      avg: 'المتوسط',
      max: 'الأقصى',
      min: 'الأدنى',
    }
  };

  const trans = translations[language];

  const getSensorStats = (data) => {
    const current = data[data.length - 1];
    const avg = (data.reduce((a, b) => a + b) / data.length).toFixed(1);
    const max = Math.max(...data).toFixed(1);
    const min = Math.min(...data).toFixed(1);
    return { current, avg, max, min };
  };

  const SimpleLineChart = ({ data, color, height = 200 }) => {
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    
    const points = data.map((value, i) => {
      const x = (i / (data.length - 1)) * 100;
      const y = 100 - ((value - min) / range) * 100;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg viewBox="0 0 100 100" height={height} style={{ width: '100%', marginTop: '10px' }}>
        <polyline points={points} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
        <polyline points={points + ' 100,100 0,100'} fill={color} opacity="0.1" />
      </svg>
    );
  };

  if (!bridgeId) {
    return <div className="sensor-monitor"><div className="card"><p>Please select a bridge</p></div></div>;
  }

  if (error) {
    return <div className="sensor-monitor"><div className="card"><p className="error-message">Error: {error}</p></div></div>;
  }

  if (!sensorData || !sensorData.temperature?.length) {
    return <div className="sensor-monitor"><div className="card"><p>Loading...</p></div></div>;
  }

  const temperatureStats = getSensorStats(sensorData.temperature);
  const moistureStats = getSensorStats(sensorData.moisture);
  const vibrationStats = getSensorStats(sensorData.vibration);
  const strainStats = getSensorStats(sensorData.strain);

  return (
    <div className="sensor-monitor">
      <div className="sensor-controls">
        <label>{trans.timeRange}:</label>
        <div className="button-group">
          {['1h', '6h', '24h', '7d'].map(range => (
            <button
              key={range}
              className={`btn-small ${timeRange === range ? 'active' : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range === '1h' ? trans.lastHour :
               range === '24h' ? trans.lastDay :
               range === '7d' ? trans.lastWeek : '6h'}
            </button>
          ))}
        </div>
      </div>

      <div className="sensor-grid">
        <div className="card sensor-card">
          <div className="card-header">{trans.temperature}</div>
          <SimpleLineChart data={sensorData.temperature} color="#ef4444" />
          <div className="sensor-stats">
            <div className="stat">
              <span>{trans.current}: {temperatureStats.current}°C</span>
            </div>
            <div className="stat">
              <span>{trans.avg}: {temperatureStats.avg}°C</span>
            </div>
            <div className="stat">
              <span>{trans.max}: {temperatureStats.max}°C</span>
            </div>
          </div>
        </div>

        <div className="card sensor-card">
          <div className="card-header">{trans.moisture}</div>
          <SimpleLineChart data={sensorData.moisture} color="#3b82f6" />
          <div className="sensor-stats">
            <div className="stat">
              <span>{trans.current}: {moistureStats.current}%</span>
            </div>
            <div className="stat">
              <span>{trans.avg}: {moistureStats.avg}%</span>
            </div>
            <div className="stat">
              <span>{trans.max}: {moistureStats.max}%</span>
            </div>
          </div>
        </div>

        <div className="card sensor-card">
          <div className="card-header">{trans.vibration}</div>
          <SimpleLineChart data={sensorData.vibration} color="#f59e0b" />
          <div className="sensor-stats">
            <div className="stat">
              <span>{trans.current}: {vibrationStats.current}g</span>
            </div>
            <div className="stat">
              <span>{trans.avg}: {vibrationStats.avg}g</span>
            </div>
            <div className="stat">
              <span>{trans.max}: {vibrationStats.max}g</span>
            </div>
          </div>
        </div>

        <div className="card sensor-card">
          <div className="card-header">{trans.strain}</div>
          <SimpleLineChart data={sensorData.strain} color="#10b981" />
          <div className="sensor-stats">
            <div className="stat">
              <span>{trans.current}: {strainStats.current}μ</span>
            </div>
            <div className="stat">
              <span>{trans.avg}: {strainStats.avg}μ</span>
            </div>
            <div className="stat">
              <span>{trans.max}: {strainStats.max}μ</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card alerts-card">
        <div className="card-header">{trans.alerts}</div>
        <div className="alerts-list">
          <p className="no-alerts">{trans.noAlerts}</p>
        </div>
      </div>
    </div>
  );
}
