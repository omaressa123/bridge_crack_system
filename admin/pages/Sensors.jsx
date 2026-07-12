import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { adminApi } from '../api/adminApi';
import { authenticatedFetch, API_URL } from '../../api';
import { DataTable, ErrorBanner, LoadingSpinner } from '../components/AdminUI';

export default function SensorsPage() {
  const [sensors, setSensors] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [live, setLive] = useState(false);

  const load = async () => {
    try {
      setSensors(await adminApi.listSensors());
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    const ws = new WebSocket(`ws://localhost:8000/ws?token=${encodeURIComponent(token)}`);
    ws.onopen = () => setLive(true);
    ws.onclose = () => setLive(false);
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setChartData((prev) => [...prev.slice(-29), {
          time: new Date().toLocaleTimeString(),
          temp: data.temperature_c,
          moisture: data.moisture_percent,
        }]);
      } catch { /* ignore */ }
    };
    return () => ws.close();
  }, []);

  const loadSensorHistory = async (bridgeId) => {
    const res = await authenticatedFetch(`${API_URL}/sensors/data?bridge_id=${bridgeId}&limit=20&time_range=24h`);
    if (!res.ok) return;
    const data = await res.json();
    setChartData(data.timestamps.map((t, i) => ({
      time: new Date(t).toLocaleTimeString(),
      temp: data.temperature_history[i],
      moisture: data.moisture_history[i],
    })));
  };

  const columns = [
    { key: 'device_id', label: 'Device' },
    { key: 'bridge_name', label: 'Bridge' },
    { key: 'status', label: 'MQTT Status', render: (s) => (
      <span className={`admin-pill ${s.status === 'connected' ? 'success' : 'danger'}`}>{s.status}</span>
    )},
    { key: 'last_seen', label: 'Last Seen', render: (s) => s.last_seen ? new Date(s.last_seen).toLocaleString() : '—' },
    { key: 'battery_level', label: 'Battery', render: (s) => s.battery_level != null ? `${s.battery_level}%` : '—' },
    { key: 'actions', label: '', render: (s) => (
      <button type="button" className="admin-btn admin-btn-sm" onClick={() => loadSensorHistory(s.bridge_id)}>History</button>
    )},
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <div className="admin-toolbar">
        <span className={`admin-pill ${live ? 'success' : 'danger'}`}>{live ? 'Live WS' : 'WS Disconnected'}</span>
        <button type="button" className="admin-btn" onClick={async () => { await adminApi.reconnectSensors(); load(); }}>Reconnect MQTT</button>
      </div>
      <DataTable columns={columns} rows={sensors} emptyMessage="No sensor devices registered" />
      {chartData.length > 0 && (
        <section className="admin-section">
          <h2>Sensor History</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#313244" />
              <XAxis dataKey="time" stroke="#A6ADC8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#A6ADC8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1E1E2E', border: '1px solid #313244' }} />
              <Line type="monotone" dataKey="temp" stroke="#8B5CF6" name="Temp °C" dot={false} />
              <Line type="monotone" dataKey="moisture" stroke="#10B981" name="Moisture %" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </section>
      )}
    </div>
  );
}
