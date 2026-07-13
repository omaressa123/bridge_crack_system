import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { authenticatedFetch, API_URL } from '../api';

// Helper to handle Leaflet invalidation size when rendered dynamically/tabs
function MapInvalidateSize() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}

// Severity → colour mapping matching application-wide CSS variable palette
const SEVERITY_COLORS = {
  0: '#10B981', // no cracks → green (success)
  1: '#10B981', // low → green (success)
  2: '#F59E0B', // medium → orange (warning)
  3: '#EF4444', // high → red (danger)
};

const SEVERITY_LABELS = {
  en: { 0: 'No cracks', 1: 'Low', 2: 'Medium', 3: 'High' },
  ar: { 0: 'لا شروخ', 1: 'منخفض', 2: 'متوسط', 3: 'عالي' },
};

export default function BridgeMap({ language }) {
  const [bridges, setBridges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isRtl = language === 'ar';

  const t = {
    en: {
      title: 'Fleet Risk Map',
      subtitle: 'All bridges colored by current severity',
      cracks: 'Total cracks',
      highSev: 'High-severity cracks',
      severity: 'Risk level',
      rec: 'Recommendation',
      loading: 'Loading map data…',
    },
    ar: {
      title: 'خريطة مخاطر الجسور',
      subtitle: 'جميع الجسور ملونة حسب مستوى الخطورة الحالي',
      cracks: 'إجمالي الشروخ',
      highSev: 'الشروخ عالية الخطورة',
      severity: 'مستوى الخطر',
      rec: 'التوصية',
      loading: 'جاري تحميل بيانات الخريطة…',
    },
  }[language] || {
    title: 'Fleet Risk Map',
    subtitle: 'All bridges colored by current severity',
    cracks: 'Total cracks', highSev: 'High-severity cracks',
    severity: 'Risk level', rec: 'Recommendation', loading: 'Loading map data…',
  };

useEffect(() => {
  const loadData = async () => {
    try {
      const response = await authenticatedFetch(`${API_URL}/bridges/map`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      console.log("Map API:", data);

      setBridges(data.bridges || []);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  loadData();
}, []);

  if (loading) {
    return (
      <div className="bridge-map-page" style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <div className="spinner" />
        <p style={{ marginLeft: 12 }}>{t.loading}</p>
      </div>
    );
  }

  if (error) {
    return <div style={{ padding: 20, color: '#e53e3e' }}>⚠️ {error}</div>;
  }

  // Centre on Cairo
  const mapCenter = [30.06, 31.22];

  return (
    <div className="bridge-map-page" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="card" style={{ marginBottom: 0 }}>
        <div className="card-header">
          🗺️ {t.title}
          <span style={{ fontSize: '0.78rem', fontWeight: 400, color: '#718096', marginLeft: 8 }}>
            {t.subtitle}
          </span>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 16, padding: '8px 16px', flexWrap: 'wrap' }}>
          {[1, 2, 3].map(s => (
            <span key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem' }}>
              <span style={{
                width: 12, height: 12, borderRadius: '50%',
                background: SEVERITY_COLORS[s], display: 'inline-block',
              }} />
              {SEVERITY_LABELS[language]?.[s] || SEVERITY_LABELS.en[s]}
            </span>
          ))}
        </div>
      </div>

      {/* Map */}
      <div style={{ height: 380, borderRadius: '0 0 12px 12px', overflow: 'hidden', position: 'relative', zIndex: 1 }}>
        <MapContainer
          center={mapCenter}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={false}
        >
          <MapInvalidateSize />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {bridges
            .filter(b => b.latitude !== null && b.latitude !== undefined && b.longitude !== null && b.longitude !== undefined)
            .map(bridge => {
              const color = SEVERITY_COLORS[bridge.max_severity] || SEVERITY_COLORS[0];
              const sevLabel = SEVERITY_LABELS[language]?.[bridge.max_severity]
                ?? SEVERITY_LABELS.en[bridge.max_severity] ?? '—';

              return (
                <CircleMarker
                  key={bridge.id}
                  center={[bridge.latitude, bridge.longitude]}
                  radius={18}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.75,
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div style={{ minWidth: 170, fontFamily: 'inherit', fontSize: '0.85rem' }}>
                      <strong style={{ fontSize: '0.95rem', display: 'block', marginBottom: 4 }}>
                        {bridge.name}
                      </strong>
                      <div>📍 {bridge.city}</div>
                      <div>
                        <span
                          style={{
                            display: 'inline-block', marginTop: 6, padding: '2px 8px',
                            borderRadius: 10, fontSize: '0.78rem', fontWeight: 700,
                            background: color + '25', color: color,
                          }}
                        >
                          {t.severity}: {sevLabel}
                        </span>
                      </div>
                      <div style={{ marginTop: 6, color: '#4a5568' }}>
                        🔍 {t.cracks}: {bridge.total_cracks}<br />
                        ⚠️ {t.highSev}: {bridge.high_severity_cracks}
                      </div>
                      <div style={{ marginTop: 4, color: '#718096', fontSize: '0.78rem' }}>
                        💡 {bridge.recommendation}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
        </MapContainer>
      </div>

      {/* Bridge list summary below map */}
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {bridges.map(bridge => {
          const color = SEVERITY_COLORS[bridge.max_severity] || SEVERITY_COLORS[0];
          const sevLabel = SEVERITY_LABELS[language]?.[bridge.max_severity]
            ?? SEVERITY_LABELS.en[bridge.max_severity] ?? '—';
          return (
            <div
              key={bridge.id}
              className="card"
              style={{ borderLeft: `4px solid ${color}`, margin: 0, padding: '10px 14px' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '0.9rem' }}>{bridge.name}</strong>
                <span style={{
                  padding: '2px 10px', borderRadius: 10, fontSize: '0.78rem',
                  fontWeight: 700, background: color + '20', color,
                }}>
                  {sevLabel}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#718096', marginTop: 2 }}>
                🔍 {bridge.total_cracks} {t.cracks} · ⚠️ {bridge.high_severity_cracks} {t.highSev}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
