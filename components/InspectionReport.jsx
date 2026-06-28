import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

export default function InspectionReport({ language, t, bridgeId }) {
  const [reports, setReports] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [error, setError] = useState(null);

  const translations = {
    en: {
      reports: 'Inspection Reports',
      generateReport: 'Generate Report',
      reportDate: 'Report Date',
      bridgeName: 'Bridge Name',
      totalCracks: 'Total Cracks',
      highSeverity: 'High Severity',
      rating: 'Rating',
      engineerName: 'Engineer',
      notes: 'Notes',
      recommendation: 'Recommendation',
      viewDetails: 'View Details',
      download: 'Download PDF',
      share: 'Share Report',
      noReports: 'No reports available',
      generating: 'Generating Report...',
      reportGenerated: 'Report generated successfully',
      newReport: 'New Report',
      details: 'Report Details',
      close: 'Close',
    },
    ar: {
      reports: 'تقارير الفحص',
      generateReport: 'إنشاء تقرير',
      reportDate: 'تاريخ التقرير',
      bridgeName: 'اسم الجسر',
      totalCracks: 'إجمالي الشروخ',
      highSeverity: 'شدة عالية',
      rating: 'التقييم',
      engineerName: 'المهندس',
      notes: 'الملاحظات',
      recommendation: 'التوصية',
      viewDetails: 'عرض التفاصيل',
      download: 'تحميل PDF',
      share: 'مشاركة التقرير',
      noReports: 'لا توجد تقارير متاحة',
      generating: 'جاري إنشاء التقرير...',
      reportGenerated: 'تم إنشاء التقرير بنجاح',
      newReport: 'تقرير جديد',
      details: 'تفاصيل التقرير',
      close: 'إغلاق',
    }
  };

  const trans = translations[language];

  useEffect(() => {
    if (!bridgeId) return;
    
    const fetchReports = async () => {
      try {
        const response = await fetch(`${API_URL}/bridge/${bridgeId}/reports`);
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
          setReports([]);
        } else {
          setError(null);
          setReports(data.reports.map(report => ({
            id: report.id,
            date: report.date,
            bridgeName: 'Bridge',
            totalCracks: report.total_cracks,
            highSeverity: report.high_severity,
            overallRating: report.high_severity > 0 ? 3 : 2,
            engineerName: 'Engineer',
            notes: 'Inspection report',
            recommendation: 'Monitor regularly',
          })));
        }
        
      } catch (error) {
        console.error('Failed to fetch reports:', error);
        setError('Failed to load reports');
      }
    };
    
    fetchReports();
  }, [bridgeId]);

  const handleGenerateReport = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      alert(trans.reportGenerated);
    }, 2000);
  };

  const handleDownloadPDF = async (reportId) => {
    try {
      const response = await fetch(
        `${API_URL}/report/${reportId}/pdf`
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Report_${reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('PDF download failed:', error);
    }
  };

  const handleShareReport = (reportId) => {
    // Simulate report sharing
    alert('Sharing options: Email, WhatsApp, SMS');
  };

  const getRatingEmoji = (rating) => {
    const emojis = { 1: '✅', 2: '⚠️', 3: '🚨' };
    return emojis[rating] || '?';
  };

  if (!bridgeId) {
    return <div className="inspection-report"><div className="card"><p>Please select a bridge</p></div></div>;
  }

  if (error) {
    return <div className="inspection-report"><div className="card"><p className="error-message">Error: {error}</p></div></div>;
  }

  return (
    <div className="inspection-report">
      <div className="report-actions">
        <button 
          className="btn-primary"
          onClick={handleGenerateReport}
          disabled={isGenerating}
        >
          {isGenerating ? trans.generating : trans.generateReport}
        </button>
      </div>

      <div className="reports-list">
        {reports.length > 0 ? (
          reports.map((report) => (
            <div key={report.id} className="card report-card">
              <div className="report-header">
                <div className="report-date">
                  <span className="date-label">{trans.reportDate}</span>
                  <h3>{report.date}</h3>
                </div>
                <div className="report-rating">
                  {getRatingEmoji(report.overallRating)}
                </div>
              </div>

              <div className="report-content">
                <div className="info-row">
                  <span className="label">{trans.bridgeName}</span>
                  <span className="value">{report.bridgeName}</span>
                </div>

                <div className="info-row">
                  <span className="label">{trans.engineerName}</span>
                  <span className="value">{report.engineerName}</span>
                </div>

                <div className="stats-row">
                  <div className="stat">
                    <span className="stat-number">{report.totalCracks}</span>
                    <span className="stat-label">{trans.totalCracks}</span>
                  </div>
                  <div className="stat highlight">
                    <span className="stat-number">{report.highSeverity}</span>
                    <span className="stat-label">{trans.highSeverity}</span>
                  </div>
                </div>

                <div className="info-row">
                  <span className="label">{trans.recommendation}</span>
                  <span className="value">{report.recommendation}</span>
                </div>

                <div className="notes">
                  <span className="label">{trans.notes}</span>
                  <p>{report.notes}</p>
                </div>

                <div className="report-actions-buttons">
                  <button 
                    className="btn-small secondary"
                    onClick={() => setSelectedReport(report)}
                  >
                    👁️ {trans.viewDetails}
                  </button>
                  <button 
                    className="btn-small secondary"
                    onClick={() => handleDownloadPDF(report.id)}
                  >
                    📥 {trans.download}
                  </button>
                  <button 
                    className="btn-small secondary"
                    onClick={() => handleShareReport(report.id)}
                  >
                    📤 {trans.share}
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="card">
            <p className="no-data">{trans.noReports}</p>
          </div>
        )}
      </div>

      {selectedReport && (
        <div className="modal-overlay" onClick={() => setSelectedReport(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{trans.details}</h2>
              <button className="close-btn" onClick={() => setSelectedReport(null)}>✕</button>
            </div>
            
            <div className="modal-body">
              <div className="detail-section">
                <h3>{trans.reportDate}: {selectedReport.date}</h3>
                <p>{selectedReport.bridgeName}</p>
              </div>

              <div className="detail-section">
                <h4>{trans.totalCracks}</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span>{trans.totalCracks}: {selectedReport.totalCracks}</span>
                  </div>
                  <div className="detail-item">
                    <span>{trans.highSeverity}: {selectedReport.highSeverity}</span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h4>{trans.notes}</h4>
                <p>{selectedReport.notes}</p>
              </div>

              <div className="detail-section">
                <h4>{trans.recommendation}</h4>
                <p className="recommendation">{selectedReport.recommendation}</p>
              </div>

              <div className="modal-actions">
                <button className="btn-primary" onClick={() => handleDownloadPDF(selectedReport.id)}>
                  📥 {trans.download}
                </button>
                <button className="btn-secondary" onClick={() => setSelectedReport(null)}>
                  {trans.close}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
