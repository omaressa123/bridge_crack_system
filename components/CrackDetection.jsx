import React, { useState } from 'react';

const API_URL = 'http://localhost:8000';

export default function CrackDetection({ language, t, bridgeId }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [cracks, setCracks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

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
    }
  };

  const trans = translations[language];

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setSelectedImage(event.target.result);
        setCracks([]);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDetectCracks = async () => {
    if (!selectedImage) return;
    
    setLoading(true);
    
    try {
      // Convert image to FormData
      const blob = await (await fetch(selectedImage)).blob();
      const formData = new FormData();
      formData.append('image', blob, 'image.jpg');
      
      // Send to backend
      const response = await fetch(`${API_URL}/detect`, {
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
      const response = await fetch(`${API_URL}/detect/${bridgeId}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cracks)
      });
      
      const data = await response.json();
      
      if (data.error) {
        alert(data.error);
      } else {
        alert(trans.savedSuccessfully);
        setCracks([]);
        setSelectedImage(null);
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
                  </div>
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
