import React from 'react';
import { authenticatedFetch } from '../../api';
import { adminApi } from '../api/adminApi';

async function downloadAuth(url, filename) {
  const res = await authenticatedFetch(url);
  if (!res.ok) throw new Error('Download failed');
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
}

export default function ReportsPage() {
  return (
    <div className="admin-section">
      <h2>Generate Reports</h2>
      <div className="admin-report-grid">
        <div className="admin-report-card">
          <h3>Inspection Report (PDF)</h3>
          <p>Fleet-wide inspection summary with crack counts per bridge.</p>
          <button type="button" className="admin-btn primary" onClick={() => downloadAuth(adminApi.downloadInspectionPdf(), 'inspection_report.pdf')}>
            Download PDF
          </button>
        </div>
        <div className="admin-report-card">
          <h3>Maintenance Report (Excel)</h3>
          <p>High-severity cracks requiring maintenance attention.</p>
          <button type="button" className="admin-btn primary" onClick={() => downloadAuth(adminApi.downloadMaintenanceExcel(), 'maintenance_report.xlsx')}>
            Download Excel
          </button>
        </div>
      </div>
    </div>
  );
}
