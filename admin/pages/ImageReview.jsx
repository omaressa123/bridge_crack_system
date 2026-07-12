import React, { useEffect, useRef, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { authenticatedFetch } from '../../api';
import { ErrorBanner, LoadingSpinner } from '../components/AdminUI';

export default function ImageReviewPage() {
  const [reviews, setReviews] = useState([]);
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [notes, setNotes] = useState('');
  const [severity, setSeverity] = useState(2);
  const canvasRef = useRef(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await adminApi.listImageReviews('pending');
      setReviews(data);
      if (data.length && !current) setCurrent(data[0]);
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (!current) return;
    let revoked = false;
    (async () => {
      const res = await authenticatedFetch(adminApi.reviewImageUrl(current.id));
      if (!res.ok) return;
      const blob = await res.blob();
      if (!revoked) setImageUrl(URL.createObjectURL(blob));
    })();
    setNotes(current.notes || '');
    setSeverity(current.severity || 2);
    return () => { revoked = true; };
  }, [current]);

  useEffect(() => {
    if (!imageUrl || !current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      const boxes = current.bounding_boxes || [];
      boxes.forEach((box) => {
        ctx.strokeStyle = '#EF4444';
        ctx.lineWidth = 3;
        const x = (box.x || 0) - (box.width || 0) / 2;
        const y = (box.y || 0) - (box.height || 0) / 2;
        ctx.strokeRect(x, y, box.width || 0, box.height || 0);
        ctx.fillStyle = '#EF4444';
        ctx.font = '14px sans-serif';
        const conf = box.confidence ? `${(box.confidence * 100).toFixed(0)}%` : '';
        ctx.fillText(`${box.label || 'crack'} ${conf}`, x, y - 4);
      });
    };
    img.src = imageUrl;
  }, [imageUrl, current]);

  const decide = async (decision) => {
    if (!current) return;
    try {
      const boxes = current.bounding_boxes || [];
      const w = boxes[0]?.width;
      const h = boxes[0]?.height;
      await adminApi.decideReview(current.id, {
        decision,
        bounding_boxes: boxes,
        severity,
        width: w,
        height: h,
        area: w && h ? w * h : undefined,
        notes,
      });
      const next = reviews.filter((r) => r.id !== current.id);
      setReviews(next);
      setCurrent(next[0] || null);
      setImageUrl('');
    } catch (e) {
      setError(e.message);
    }
  };

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await adminApi.uploadForReview(file);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner />;
  return (
    <div className="review-page">
      <ErrorBanner message={error} onRetry={load} />
      <div className="admin-toolbar">
        <label className="admin-btn primary admin-file-btn">
          Upload Image
          <input type="file" accept="image/*" hidden onChange={upload} />
        </label>
        <span className="admin-muted">{reviews.length} pending</span>
      </div>
      {current ? (
        <div className="review-layout">
          <div className="review-canvas-wrap">
            <canvas ref={canvasRef} className="review-canvas" />
          </div>
          <aside className="review-panel">
            <h3>YOLO Prediction</h3>
            <p>Confidence: <strong>{current.confidence ? `${(current.confidence * 100).toFixed(1)}%` : 'N/A'}</strong></p>
            <p>Boxes: <strong>{(current.bounding_boxes || []).length}</strong></p>
            <ul className="review-box-list">
              {(current.bounding_boxes || []).map((b, i) => (
                <li key={i}>{b.label} — {(b.confidence * 100).toFixed(0)}% @ ({b.x?.toFixed(0)}, {b.y?.toFixed(0)})</li>
              ))}
            </ul>
            <label>Severity
              <select value={severity} onChange={(e) => setSeverity(Number(e.target.value))}>
                <option value={1}>Low</option>
                <option value={2}>Medium</option>
                <option value={3}>High</option>
              </select>
            </label>
            <label>Notes<textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} /></label>
            <div className="review-actions">
              <button type="button" className="admin-btn success large" onClick={() => decide('crack')}>✔ Crack</button>
              <button type="button" className="admin-btn danger large" onClick={() => decide('no_crack')}>✔ No Crack</button>
            </div>
          </aside>
        </div>
      ) : (
        <p className="admin-empty">No pending images to review. Upload one to get started.</p>
      )}
    </div>
  );
}
