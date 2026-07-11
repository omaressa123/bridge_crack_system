import React, { useState, useEffect, useCallback } from 'react';
import { authenticatedFetch, API_URL } from '../api';
import CrackGrowthChart from './CrackGrowthChart';


export default function CrackDetection({ language, t, bridgeId }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [cracks, setCracks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [detectionAttempted, setDetectionAttempted] = useState(false);
  const [selectedCrackId, setSelectedCrackId] = useState(null);
  const [trackedCracks, setTrackedCracks] = useState([]);
  const [trackedLoading, setTrackedLoading] = useState(false);

  const translations = {
    en: {
      uploadPhoto: 'Upload Photo',
      selectImage: 'Select Image from Device',
      takePhoto: 'Take Photo with Camera',
      detectCracks: 'Detect Cracks',
      noImage: 'No image selected',
      loading: 'Analyzing image...',
      crackCount: 'Cracks Found',
      confidence: 'Confidence',
      severity: 'Severity',
      location: 'Location',
      coordinates: 'Coordinates',
      confirm: 'Confirm Detection',
      reject: 'Reject Detection',
      confirmed: 'Confirmed by Engineer',
      needsReview: 'Needs Review',
      hairline: 'Hairline Crack',
      spalling: 'Spalling',
      structural: 'Structural Crack',
      details: 'Crack Details',
      saveDetections: 'Save Detections',
      saving: 'Saving...',
      savedSuccessfully: 'Detections saved successfully!',
      noCracksDetected: 'The model cannot detect this image. Please connect with the engineering support to solve the problem.',
      viewHistory: 'View Growth History',
      hideHistory: 'Hide History',
      trackedCracks: 'Tracked Cracks',
      trackedSubtitle: 'Cracks with multi-inspection history on this bridge',
      noTrackedCracks: 'No tracked cracks yet. Run seed data or save repeated detections.',
      inspections: 'inspections',
      demoCrack: 'Demo lineage crack',
    },
    ar: {
      uploadPhoto: 'تحميل صورة',
      selectImage: 'اختر صورة من الجهاز',
      takePhoto: 'التقط صورة بالكاميرا',
      detectCracks: 'كشف الشروخ',
      noImage: 'لم يتم اختيار صورة',
      loading: 'جاري تحليل الصورة...',
      crackCount: 'الشروخ المكتشفة',
      confidence: 'الثقة',
      severity: 'الشدة',
      location: 'الموقع',
      coordinates: 'الإحداثيات',
      confirm: 'تأكيد الكشف',
      reject: 'رفض الكشف',
      confirmed: 'تم التأكيد من قبل المهندس',
      needsReview: 'يحتاج إلى مراجعة',
      hairline: 'شرخ رفيع',
      spalling: 'تقشير',
      structural: 'شرخ هيكلي',
      details: 'تفاصيل الشرخ',
      saveDetections: 'حفظ الكشوفات',
      saving: 'جاري الحفظ...',
      savedSuccessfully: 'تم حفظ الكشوفات بنجاح!',
      noCracksDetected: 'النموذج لا يستطيع اكتشاف هذه الصورة. يرجى الاتصال بالدعم الفني لحل المشكلة.',
      viewHistory: 'عرض تاريخ النمو',
      hideHistory: 'إخفاء التاريخ',
      trackedCracks: 'الشروخ المتتبعة',
      trackedSubtitle: 'شروخ لها سجل فحوصات متعددة على هذا الجسر',
      noTrackedCracks: 'لا توجد شروخ متتبعة بعد. شغّل بيانات التجربة أو احفظ كشوفات متكررة.',
      inspections: 'فحوصات',
      demoCrack: 'شرخ تجريبي للعرض',
    }
  };


  const trans = translations[language];

  const fetchTrackedCracks = useCallback(async () => {
    if (!bridgeId) return;
    setTrackedLoading(true);
    try {
      const response = await authenticatedFetch(`${API_URL}/bridge/${bridgeId}/crack-growth`);
      const data = await response.json();
      if (data.crack_history) {
        const tracked = Object.entries(data.crack_history)
          .filter(([, entries]) => entries.length >= 2)
          .map(([identifier, entries]) => ({
            identifier,
            latestId: entries[entries.length - 1].id,
            inspectionCount: entries.length,
            latestArea: entries[entries.length - 1].area,
            crackType: entries[entries.length - 1].crack_type,
            isDemo: identifier === 'CRK-CAIRO12-001',
          }))
          .sort((a, b) => b.inspectionCount - a.inspectionCount);
        setTrackedCracks(tracked);
      }
    } catch (error) {
      console.error('Failed to fetch tracked cracks:', error);
    } finally {
      setTrackedLoading(false);
    }
  }, [bridgeId]);

  useEffect(() => {
    fetchTrackedCracks();
  }, [fetchTrackedCracks]);

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setSelectedImage(event.target.result);
        setCracks([]);
        setDetectionAttempted(false);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDetectCracks = async () => {
    if (!selectedImage) return;
    
    setLoading(true);
    setDetectionAttempted(true);
    
    try {
      // Convert image to FormData
      const blob = await (await fetch(selectedImage)).blob();
      const formData = new FormData();
      formData.append('image', blob, 'image.jpg');
      
      // Send to backend
      const response = await authenticatedFetch(`${API_URL}/detect`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      // Convert backend response to app format
      const cracksFormatted = data.cracks.map((crack, i) => ({
        id: i + 1,
        x: Math.round(crack.x),
        y: Math.round(crack.y),
        width: Math.round(crack.width),
        height: Math.round(crack.height),
        confidence: crack.confidence,
        severity: crack.severity,
        type: crack.crack_type,
        confirmed: false
      }));
      
      setCracks(cracksFormatted);
      setLoading(false);
      
    } catch (error) {
      console.error('Detection error:', error);
      setLoading(false);
      alert('Error detecting cracks. Is backend running?');
    }
  };

  const handleSaveDetections = async () => {
    if (!bridgeId || cracks.length === 0) return;

    setSaving(true);
    
    try {
      const response = await authenticatedFetch(`${API_URL}/detect/${bridgeId}/save`, {
        method: 'POST',
        body: JSON.stringify(cracks)
      });
      
      const data = await response.json();
      
      if (data.error) {
        alert(data.error);
      } else {
        alert(trans.savedSuccessfully);
        setCracks([]);
        setSelectedImage(null);
        fetchTrackedCracks();
      }
      
    } catch (error) {
      console.error('Save error:', error);
      alert('Error saving detections');
    }
    
    setSaving(false);
  };

  const handleConfirmCrack = (crackId) => {
    setCracks(cracks.map(crack =>
      crack.id === crackId ? { ...crack, confirmed: true } : crack
    ));
  };

  const handleRejectCrack = (crackId) => {
    setCracks(cracks.filter(crack => crack.id !== crackId));
  };

  const getSeverityLabel = (level) => {
    const labels = {
      1: language === 'en' ? 'Low' : 'منخفض',
      2: language === 'en' ? 'Medium' : 'متوسط',
      3: language === 'en' ? 'High' : 'عالي',
    };
    return labels[level] || '';
  };

  const getCrackTypeLabel = (type) => {
    const typeMap = {
      hairline: trans.hairline,
      spalling: trans.spalling,
      structural: trans.structural,
    };
    return typeMap[type] || type;
  };

  return (
    <div className="crack-detection">
      {bridgeId && (
        <div className="tracked-cracks-section" style={{ marginBottom: 16 }}>
          <div className="card">
            <div className="card-header">
              📈 {trans.trackedCracks}
              <span style={{ fontSize: '0.78rem', fontWeight: 400, color: '#718096', marginLeft: 8 }}>
                {trans.trackedSubtitle}
              </span>
            </div>
            {trackedLoading ? (
              <p style={{ padding: '12px 16px', color: '#718096' }}>{trans.loading}</p>
            ) : trackedCracks.length === 0 ? (
              <p style={{ padding: '12px 16px', color: '#718096' }}>{trans.noTrackedCracks}</p>
            ) : (
              <div className="crack-list" style={{ padding: '8px 12px 12px' }}>
                {trackedCracks.map((tracked) => (
                  <div key={tracked.identifier} className="crack-item">
                    <div className="crack-header">
                      <span className="crack-type">
                        {tracked.isDemo ? `⭐ ${trans.demoCrack}` : tracked.identifier}
                      </span>
                      <span className="severity-badge severity-2">
                        {tracked.inspectionCount} {trans.inspections}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#718096', marginTop: 4 }}>
                      {getCrackTypeLabel(tracked.crackType)} · {Math.round(tracked.latestArea).toLocaleString()} px²
                    </div>
                    <div className="crack-actions">
                      <button
                        className="btn-small"
                        style={{ marginTop: 6, background: '#ebf8ff', color: '#2b6cb0', border: '1px solid #bee3f8' }}
                        onClick={() => setSelectedCrackId(
                          selectedCrackId === tracked.latestId ? null : tracked.latestId
                        )}
                      >
                        📈 {selectedCrackId === tracked.latestId ? trans.hideHistory : trans.viewHistory}
                      </button>
                    </div>
                    {selectedCrackId === tracked.latestId && (
                      <CrackGrowthChart crackId={tracked.latestId} language={language} />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="upload-section">
        <div className="card">
          <div className="card-header">{trans.uploadPhoto}</div>
          
          <div className="upload-controls">
            <label htmlFor="image-input" className="upload-btn primary">
              📁 {trans.selectImage}
            </label>
            <input
              id="image-input"
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              style={{ display: 'none' }}
            />
            
            <button className="upload-btn secondary">
              📷 {trans.takePhoto}
            </button>
          </div>

          {selectedImage && (
            <div className="image-preview">
              <img src={selectedImage} alt="Preview" />
              <button 
                className="btn-primary"
                onClick={handleDetectCracks}
                disabled={loading}
              >
                {loading ? trans.loading : trans.detectCracks}
              </button>
            </div>
          )}

          {!selectedImage && (
            <div className="no-image">
              <p>📸 {trans.noImage}</p>
            </div>
          )}
        </div>
      </div>

      {detectionAttempted && cracks.length === 0 && (
        <div className="results-section">
          <div className="card">
            <div className="card-header" style={{ color: '#ff6b6b' }}>
              ⚠️ Detection Result
            </div>
            <div style={{ padding: '20px', textAlign: 'center', color: '#4a5568', lineHeight: '1.6' }}>
              <p>{trans.noCracksDetected}</p>
            </div>
          </div>
        </div>
      )}

      {cracks.length > 0 && (
        <div className="results-section">
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{trans.crackCount}: {cracks.length}</span>
              <button 
                className="btn-primary" 
                onClick={handleSaveDetections} 
                disabled={saving}
              >
                {saving ? trans.saving : trans.saveDetections}
              </button>
            </div>

            <div className="crack-list">
              {cracks.map((crack) => (
                <div key={crack.id} className="crack-item">
                  <div className="crack-header">
                    <span className="crack-type">{getCrackTypeLabel(crack.type)}</span>
                    <span className={`severity-badge severity-${crack.severity}`}>
                      {getSeverityLabel(crack.severity)}
                    </span>
                  </div>

                  <div className="crack-metrics">
                    <div className="metric">
                      <span className="metric-label">{trans.confidence}</span>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${crack.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="metric-value">{(crack.confidence * 100).toFixed(0)}%</span>
                    </div>

                    <div className="metric">
                      <span className="metric-label">{trans.location}</span>
                      <p>{trans.coordinates}: ({crack.x}, {crack.y})</p>
                    </div>
                  </div>

                  <div className="crack-actions">
                    {crack.confirmed ? (
                      <span className="badge confirmed">✓ {trans.confirmed}</span>
                    ) : (
                      <>
                        <button
                          className="btn-small confirm"
                          onClick={() => handleConfirmCrack(crack.id)}
                        >
                          ✓ {trans.confirm}
                        </button>
                        <button
                          className="btn-small reject"
                          onClick={() => handleRejectCrack(crack.id)}
                        >
                          ✗ {trans.reject}
                        </button>
                      </>
                    )}
                    {/* Feature 1 & 2: Toggle growth history / prediction */}
                    {crack.dbId && (
                      <button
                        className="btn-small"
                        style={{ marginTop: 6, background: '#ebf8ff', color: '#2b6cb0', border: '1px solid #bee3f8' }}
                        onClick={() => setSelectedCrackId(
                          selectedCrackId === crack.dbId ? null : crack.dbId
                        )}
                      >
                        📈 {selectedCrackId === crack.dbId ? trans.hideHistory : trans.viewHistory}
                      </button>
                    )}
                  </div>

                  {/* Growth chart expands inline under the selected crack */}
                  {crack.dbId && selectedCrackId === crack.dbId && (
                    <CrackGrowthChart crackId={crack.dbId} language={language} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>{trans.loading}</p>
        </div>
      )}
    </div>
  );
}
