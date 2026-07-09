import React, { useState, useEffect } from 'react';

import { authenticatedFetch, API_URL } from '../api';

/**
 * Safely processes and filters sensor data to ensure only valid numbers are used
 * @param {any[]} rawData - Raw data from API (could contain null/undefined/strings)
 * @returns {number[]} Array of valid numbers
 */
const processSensorData = (rawData) => {
  if (!Array.isArray(rawData)) {
    return [];
  }
  
  return rawData
    .map(value => Number(value))
    .filter(value => !isNaN(value) && isFinite(value));
};

/**
 * Calculates safe sensor statistics, preventing crashes from invalid data
 * @param {any[]} rawData - Raw sensor data
 * @returns {Object} Statistics with safe defaults
 */
const getSensorStats = (rawData) => {
  const data = processSensorData(rawData);
  
  if (data.length === 0) {
    return {
      current: 'N/A',
      avg: 'N/A',
      max: 'N/A',
      min: 'N/A'
    };
  }

  const current = data[data.length - 1];
  const avg = (data.reduce((a, b) => a + b, 0) / data.length).toFixed(1);
  const max = Math.max(...data).toFixed(1);
  const min = Math.min(...data).toFixed(1);
  
  return { current, avg, max, min };
};

/**
 * SimpleLineChart component with full defensive programming to prevent NaN errors
 * @param {Object} props - Component props
 * @param {any[]} props.data - Sensor data array
 * @param {string} props.color - Line color
 * @param {number} [props.height=200] - SVG height
 */
const SimpleLineChart = ({ data: rawData, color, height = 200 }) => {
  // Process and filter raw data to only valid numbers
  const data = processSensorData(rawData);

  // If no valid data, show friendly placeholder
  if (data.length === 0) {
    return (
      <div style={{ 
        height: height, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#888',
        fontSize: '14px'
      }}>
        No data available
      </div>
    );
  }

  // Calculate min, max with fallback values
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min !== 0 ? max - min : 1; // Prevent division by zero

  // Generate points with safe calculations
  const points = data.map((value, i) => {
    // Safe x calculation - if only one point, center it
    let x;
    if (data.length === 1) {
      x = 50; // Center single point in 100px width
    } else {
      x = (i / (data.length - 1)) * 100;
    }

    // Safe y calculation
    const y = 100 - ((value - min) / range) * 100;

    // Ensure x and y are finite numbers (never NaN/Infinity)
    const safeX = isFinite(x) ? x : 50;
    const safeY = isFinite(y) ? y : 50;

    return `${safeX},${safeY}`;
  }).join(' ');

  return (
    <svg viewBox="0 0 100 100" height={height} style={{ width: '100%', marginTop: '10px' }}>
      <polyline 
        points={points} 
        fill="none" 
        stroke={color} 
        strokeWidth="2" 
        vectorEffect="non-scaling-stroke" 
      />
      <polyline 
        points={points + ' 100,100 0,100'} 
        fill={color} 
        opacity="0.1" 
      />
    </svg>
  );
};

export default function SensorMonitor({ language, t, bridgeId }) {
  const [sensorData, setSensorData] = useState(null);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    if (!bridgeId) return;
    
    const fetchSensorData = async () => {
      try {
        const response = await authenticatedFetch(
          `${API_URL}/sensors/data?bridge_id=${bridgeId}&limit=7`
        );
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
          setSensorData(null);
        } else {
          setError(null);
          setSensorData({
            temperature: data.temperature_history || [],
            moisture: data.moisture_history || [],
            vibration: data.vibration_history || [],
            strain: data.strain_history || [],
          });
        }
        
      } catch (error) {
        console.error('Failed to fetch sensor data:', error);
        setError('Failed to load sensor data');
      }
    };
    
    fetchSensorData();
    const interval = setInterval(fetchSensorData, 60000);
    
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
      noData: 'No sensor data available',
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
      noData: 'لا توجد بيانات من المستشعر',
    }
  };

  const trans = translations[language];

  if (!bridgeId) {
    return <div className="sensor-monitor"><div className="card"><p>Please select a bridge</p></div></div>;
  }

  if (error) {
    return <div className="sensor-monitor"><div className="card"><p className="error-message">Error: {error}</p></div></div>;
  }

  if (!sensorData) {
    return <div className="sensor-monitor"><div className="card"><p>Loading...</p></div></div>;
  }

  // Check if we have any data (process all to be safe)
  const hasData = 
    processSensorData(sensorData.temperature).length > 0 ||
    processSensorData(sensorData.moisture).length > 0 ||
    processSensorData(sensorData.vibration).length > 0 ||
    processSensorData(sensorData.strain).length > 0;

  if (!hasData) {
    return <div className="sensor-monitor"><div className="card"><p>{trans.noData}</p></div></div>;
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
