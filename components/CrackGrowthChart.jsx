import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { authenticatedFetch, API_URL } from '../api';

/**
 * CrackGrowthChart
 * ─────────────────
 * Fetches /crack/{crackId}/history and renders:
 *   • A line chart of area over time
 *   • A "+X% since first detection" summary badge
 *   • A prediction card from /crack/{crackId}/prediction
 */
export default function CrackGrowthChart({ crackId, language }) {
  const [history, setHistory] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isRtl = language === 'ar';

  const labels = {
    en: {
      title: 'Crack Growth History',
      area: 'Area (px²)',
      date: 'Date',
      noHistory: 'Not enough inspection history yet (need ≥ 2 inspections).',
      sincFirst: 'since first detection',
      inspections: 'inspections',
      prediction: 'Maintenance Prediction',
      disclaimer: 'Linear trend extrapolation — not an ML model.',
    },
    ar: {
      title: 'تاريخ نمو الشرخ',
      area: 'المساحة (px²)',
      date: 'التاريخ',
      noHistory: 'لا توجد بيانات كافية بعد (يلزم فحصان على الأقل).',
      sincFirst: 'منذ أول كشف',
      inspections: 'فحوصات',
      prediction: 'توقع الصيانة',
      disclaimer: 'استقراء خطي — وليس نموذج ذكاء اصطناعي.',
    },
  };
  const t = labels[language] || labels.en;

  useEffect(() => {
    if (!crackId) return;
    setLoading(true);
    setError(null);

    Promise.all([
      authenticatedFetch(`${API_URL}/crack/${crackId}/history`).then(r => r.json()),
      authenticatedFetch(`${API_URL}/crack/${crackId}/prediction`).then(r => r.json()),
    ])
      .then(([hist, pred]) => {
        setHistory(hist);
        setPrediction(pred);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [crackId]);

  if (!crackId) return null;
  if (loading) return <div className="chart-loading">⏳ Loading growth data…</div>;
  if (error) return <div className="chart-error">⚠️ {error}</div>;
  if (!history || history.inspection_count < 2) {
    return (
      <div className="crack-growth-card">
        <div className="card-header">{t.title}</div>
        <p style={{ padding: '12px', color: '#718096' }}>{t.noHistory}</p>
      </div>
    );
  }

  // Format chart data
  const chartData = history.history.map(h => ({
    date: new Date(h.detected_at).toLocaleDateString(),
    area: h.area,
    severity: h.severity_level,
  }));

  const growthPct = history.growth_pct;
  const isPositive = growthPct > 0;

  // Severity color for prediction card
  const predStatusColors = {
    critical_now: '#e53e3e',
    active_growth: '#dd6b20',
    no_trend: '#38a169',
    insufficient_data: '#718096',
  };
  const predColor = prediction ? predStatusColors[prediction.status] || '#718096' : '#718096';
  const predMsg = prediction
    ? (language === 'ar' ? prediction.message_ar : prediction.message_en)
    : null;

  return (
    <div className="crack-growth-card" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* ── Header ── */}
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>📈 {t.title}</span>
        {growthPct !== null && (
          <span
            className="growth-badge"
            style={{
              background: isPositive ? '#fed7d7' : '#c6f6d5',
              color: isPositive ? '#c53030' : '#276749',
              borderRadius: '12px',
              padding: '3px 10px',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            {isPositive ? '▲' : '▼'} {Math.abs(growthPct)}% {t.sincFirst}
          </span>
        )}
      </div>

      {/* ── Metadata row ── */}
      <div style={{ padding: '8px 16px', color: '#718096', fontSize: '0.8rem' }}>
        {history.inspection_count} {t.inspections} · {t.disclaimer}
      </div>

      {/* ── Line chart ── */}
      <div style={{ padding: '0 8px 8px' }}>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(v) => [`${v.toLocaleString()} px²`, t.area]}
              contentStyle={{ fontSize: '0.8rem' }}
            />
            <Line
              type="monotone"
              dataKey="area"
              stroke="#e53e3e"
              strokeWidth={2.5}
              dot={{ r: 5, fill: '#e53e3e' }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* ── Prediction card ── */}
      {prediction && (
        <div
          className="prediction-card"
          style={{
            margin: '0 12px 12px',
            padding: '10px 14px',
            borderRadius: '8px',
            borderLeft: `4px solid ${predColor}`,
            background: `${predColor}15`,
          }}
        >
          <div style={{ fontWeight: 700, color: predColor, marginBottom: '4px', fontSize: '0.88rem' }}>
            🔮 {t.prediction}
          </div>
          <div style={{ color: '#2d3748', fontSize: '0.85rem', lineHeight: 1.5 }}>{predMsg}</div>
          {prediction.recommended_inspection_date && (
            <div style={{ marginTop: '4px', fontSize: '0.78rem', color: '#718096' }}>
              📅 {prediction.recommended_inspection_date}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
