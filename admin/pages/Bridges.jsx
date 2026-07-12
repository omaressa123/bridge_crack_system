import React, { useEffect, useState } from 'react';
import { adminApi } from '../api/adminApi';
import { DataTable, ErrorBanner, LoadingSpinner, Modal } from '../components/AdminUI';

const emptyBridge = { bridge_name: '', city: '', latitude: '', longitude: '', inspection_schedule: '' };

export default function BridgesPage() {
  const [bridges, setBridges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(emptyBridge);
  const [editId, setEditId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      setBridges(await adminApi.listBridges());
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => { setForm(emptyBridge); setEditId(null); setModal('form'); };
  const openEdit = (b) => {
    setForm({
      bridge_name: b.bridge_name,
      city: b.city,
      latitude: b.latitude ?? '',
      longitude: b.longitude ?? '',
      inspection_schedule: b.inspection_schedule ?? '',
    });
    setEditId(b.id);
    setModal('form');
  };

  const save = async (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      latitude: form.latitude ? parseFloat(form.latitude) : null,
      longitude: form.longitude ? parseFloat(form.longitude) : null,
    };
    try {
      if (editId) await adminApi.updateBridge(editId, payload);
      else await adminApi.createBridge(payload);
      setModal(null);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const uploadImage = async (bridgeId, file) => {
    try {
      await adminApi.uploadBridgeImage(bridgeId, file);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'bridge_name', label: 'Name' },
    { key: 'city', label: 'City' },
    { key: 'gps', label: 'GPS', render: (b) => b.latitude != null ? `${b.latitude.toFixed(4)}, ${b.longitude?.toFixed(4)}` : '—' },
    { key: 'inspection_schedule', label: 'Schedule', render: (b) => b.inspection_schedule || '—' },
    { key: 'image', label: 'Image', render: (b) => (
      <label className="admin-file-btn">
        Upload
        <input type="file" accept="image/*" hidden onChange={(e) => e.target.files[0] && uploadImage(b.id, e.target.files[0])} />
      </label>
    )},
    { key: 'actions', label: 'Actions', render: (b) => (
      <div className="admin-actions">
        <button type="button" className="admin-btn admin-btn-sm" onClick={() => openEdit(b)}>Edit</button>
        <button type="button" className="admin-btn admin-btn-sm danger" onClick={async () => {
          if (confirm('Delete bridge?')) { await adminApi.deleteBridge(b.id); load(); }
        }}>Delete</button>
      </div>
    )},
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <ErrorBanner message={error} onRetry={load} />
      <div className="admin-toolbar">
        <button type="button" className="admin-btn primary" onClick={openCreate}>+ Add Bridge</button>
      </div>
      <DataTable columns={columns} rows={bridges} />
      {modal === 'form' && (
        <Modal title={editId ? 'Edit Bridge' : 'Add Bridge'} onClose={() => setModal(null)}>
          <form onSubmit={save} className="admin-form">
            <label>Name<input required value={form.bridge_name} onChange={(e) => setForm({ ...form, bridge_name: e.target.value })} /></label>
            <label>City<input required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></label>
            <label>Latitude<input type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} /></label>
            <label>Longitude<input type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} /></label>
            <label>Inspection Schedule<input value={form.inspection_schedule} onChange={(e) => setForm({ ...form, inspection_schedule: e.target.value })} placeholder="e.g. Monthly" /></label>
            <div className="admin-form-actions">
              <button type="submit" className="admin-btn primary">Save</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
