# 🔌 Backend Integration Guide - React App ↔ Raspberry Pi

## Overview

This guide shows how to connect your React mobile app to the FastAPI backend running on Raspberry Pi.

---

## 🎯 Integration Points

```
┌─────────────────────┐         WebSocket          ┌──────────────────┐
│  React Mobile App   │ ◄─────────────────────────► │  Raspberry Pi 4  │
│  (Browser)          │      HTTP REST API         │  (FastAPI)       │
└─────────────────────┘                            └──────────────────┘
       │                                                    │
       │ • Photo Upload                                   │
       │ • WebSocket Messages                            │ • YOLOv8 Detection
       │ • API Requests                                  │ • Sensor Data
       │ • Display Results                               │ • Database
       │                                                  │
       └──────────────────────────────────────────────────┘
```

---

## 1️⃣ WebSocket Connection Setup

### In React App (App.jsx)

Current mock setup (lines 23-40):
```javascript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws');
  
  ws.onopen = () => {
    setIsConnected(true);
    console.log('✅ Connected to Raspberry Pi');
  };
  
  ws.onerror = () => {
    setIsConnected(false);
    console.error('❌ Failed to connect');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle incoming sensor data
    console.log('📡 Received:', data);
  };
  
  return () => ws.close();
}, []);
```

### In FastAPI Backend (Python)

```python
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import WebSocketRoute
import asyncio
import json

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Mobile app connected")
    
    try:
        while True:
            # Send sensor data every 60 seconds
            sensor_data = {
                "temperature": 32,
                "moisture": 45,
                "vibration": 0.8,
                "strain": 120,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_json(sensor_data)
            await asyncio.sleep(60)  # Send every 60 seconds
            
    except WebSocketDisconnect:
        print("❌ Mobile app disconnected")
```

---

## 2️⃣ Crack Detection API

### React Component (CrackDetection.jsx)

Replace the mock function in `handleDetectCracks`:

**Current (Mock):**
```javascript
const handleDetectCracks = async () => {
  if (!selectedImage) return;
  
  setLoading(true);
  
  // Mock delay
  setTimeout(() => {
    setCracks([/* mock data */]);
    setLoading(false);
  }, 2000);
};
```

**New (Real Backend):**
```javascript
const handleDetectCracks = async () => {
  if (!selectedImage) return;
  
  setLoading(true);
  
  try {
    // Convert image to FormData
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = async () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      
      canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'image.jpg');
        
        // Send to backend
        const response = await fetch('http://192.168.1.100:8000/detect', {
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
      });
    };
    
    img.src = selectedImage;
    
  } catch (error) {
    console.error('Detection error:', error);
    setLoading(false);
    alert('Error detecting cracks. Is backend running?');
  }
};
```

### FastAPI Backend

```python
from fastapi import UploadFile, File
from PIL import Image
import io
from ultralytics import YOLO

# Load model once at startup
model = YOLO('bridge_crack_detector.pt')

@app.post("/detect")
async def detect_cracks(image: UploadFile = File(...)):
    """Detect cracks in uploaded image"""
    
    try:
        # Read image
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        
        # Run detection
        results = model(img)
        
        # Format response
        cracks = []
        for result in results:
            for box in result.boxes:
                cracks.append({
                    "x": float(box.xywh[0][0]),
                    "y": float(box.xywh[0][1]),
                    "width": float(box.xywh[0][2]),
                    "height": float(box.xywh[0][3]),
                    "confidence": float(box.conf[0]),
                    "severity": classify_severity(float(box.conf[0])),
                    "crack_type": "hairline"  # Classify as needed
                })
        
        return {"cracks": cracks}
        
    except Exception as e:
        return {"error": str(e), "cracks": []}

def classify_severity(confidence):
    """Map confidence to severity level"""
    if confidence > 0.9:
        return 3  # High
    elif confidence > 0.75:
        return 2  # Medium
    else:
        return 1  # Low
```

---

## 3️⃣ Sensor Data API

### React Component (SensorMonitor.jsx)

Add this function to fetch real sensor data:

```javascript
useEffect(() => {
  const fetchSensorData = async () => {
    try {
      const response = await fetch(
        `http://192.168.1.100:8000/sensors/data?bridge_id=${bridgeId}&limit=7`
      );
      const data = await response.json();
      
      setSensorData({
        temperature: data.temperature_history,
        moisture: data.moisture_history,
        vibration: data.vibration_history,
        strain: data.strain_history
      });
      
    } catch (error) {
      console.error('Failed to fetch sensor data:', error);
    }
  };
  
  // Fetch immediately and then every 60 seconds
  fetchSensorData();
  const interval = setInterval(fetchSensorData, 60000);
  
  return () => clearInterval(interval);
}, [bridgeId, timeRange]);
```

### FastAPI Backend

```python
from datetime import datetime, timedelta
from sqlalchemy import select

@app.get("/sensors/data")
async def get_sensor_data(bridge_id: int, limit: int = 7, time_range: str = "24h"):
    """Get sensor readings for a bridge"""
    
    # Query database for sensor data
    query = select(SensorData).where(
        SensorData.bridge_id == bridge_id
    ).order_by(
        SensorData.timestamp.desc()
    ).limit(limit)
    
    results = db.execute(query).scalars().all()
    
    # Reverse to get chronological order
    results = list(reversed(results))
    
    return {
        "temperature_history": [r.temperature_c for r in results],
        "moisture_history": [r.moisture_percent for r in results],
        "vibration_history": [r.acceleration_x for r in results],  # or magnitude
        "strain_history": [r.strain_gauge_value for r in results],
        "timestamps": [r.timestamp.isoformat() for r in results]
    }
```

---

## 4️⃣ Overall Severity API

### React Component (Dashboard.jsx)

Replace mock data with real API:

```javascript
useEffect(() => {
  const fetchBridgeStatus = async () => {
    try {
      const response = await fetch(
        `http://192.168.1.100:8000/bridge/${bridgeId}/status`
      );
      const data = await response.json();
      
      setBridgeData({
        bridge_name: data.bridge_name,
        city: data.city,
        overall_severity: data.overall_severity,  // 1, 2, or 3
        total_cracks: data.total_cracks,
        high_severity_cracks: data.high_severity_cracks,
        last_inspection: data.last_inspection_date,
        recommendation: data.recommendation,
        sensors: data.current_sensors
      });
      
    } catch (error) {
      console.error('Failed to fetch bridge status:', error);
    }
  };
  
  fetchBridgeStatus();
  const interval = setInterval(fetchBridgeStatus, 300000); // Every 5 minutes
  
  return () => clearInterval(interval);
}, [bridgeId]);
```

### FastAPI Backend

```python
@app.get("/bridge/{bridge_id}/status")
async def get_bridge_status(bridge_id: int):
    """Get overall bridge status and statistics"""
    
    # Query bridge info
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    
    # Get latest cracks
    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge_id
    ).all()
    
    # Get current sensor readings
    latest_sensor = db.query(SensorData).filter(
        SensorData.bridge_id == bridge_id
    ).order_by(SensorData.timestamp.desc()).first()
    
    # Calculate severity
    severity = calculate_overall_severity(cracks, latest_sensor)
    
    return {
        "bridge_name": bridge.bridge_name,
        "city": bridge.city,
        "overall_severity": severity,
        "total_cracks": len(cracks),
        "high_severity_cracks": len([c for c in cracks if c.severity_level >= 3]),
        "last_inspection_date": bridge.inspection_date.isoformat(),
        "recommendation": get_recommendation(severity),
        "current_sensors": {
            "temperature": latest_sensor.temperature_c,
            "moisture": latest_sensor.moisture_percent,
            "vibration": latest_sensor.acceleration_x,
            "strain": latest_sensor.strain_gauge_value
        }
    }
```

---

## 5️⃣ Report Generation API

### React Component (InspectionReport.jsx)

```javascript
const handleDownloadPDF = async (reportId) => {
  try {
    const response = await fetch(
      `http://192.168.1.100:8000/report/${reportId}/pdf`,
      { responseType: 'blob' }
    );
    
    // Create download link
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
```

### FastAPI Backend

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

@app.get("/report/{report_id}/pdf")
async def get_report_pdf(report_id: int):
    """Generate and return PDF report"""
    
    # Query report
    report = db.query(InspectionReport).filter(
        InspectionReport.id == report_id
    ).first()
    
    # Create PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Add report content
    c.drawString(100, 750, f"Bridge Inspection Report")
    c.drawString(100, 730, f"Date: {report.report_date}")
    c.drawString(100, 710, f"Bridge: {report.bridge.bridge_name}")
    c.drawString(100, 690, f"Total Cracks: {report.total_cracks_detected}")
    c.drawString(100, 670, f"High Severity: {report.high_severity_cracks}")
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
    )
```

---

## 6️⃣ CORS Configuration

Add to FastAPI backend so React can make requests:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For production, restrict to specific origins:
# allow_origins=["http://192.168.1.50:5173"],
```

---

## 🔗 API Endpoints Summary

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `ws://host:8000/ws` | WS | Real-time sensor data | 🟡 |
| `/detect` | POST | Crack detection | 🟡 |
| `/sensors/data` | GET | Sensor history | 🟡 |
| `/bridge/{id}/status` | GET | Bridge status | 🟡 |
| `/report/{id}/pdf` | GET | PDF download | 🟡 |

Legend: 🟢 Ready | 🟡 Needs implementation | 🔴 Not started

---

## 📋 Implementation Checklist

### Before Going Live:

- [ ] **Network Setup**
  - [ ] Find Raspberry Pi IP address
  - [ ] Ensure RPi and phone on same WiFi
  - [ ] Test ping from phone to RPi

- [ ] **Backend Endpoints**
  - [ ] Implement `/detect` endpoint
  - [ ] Implement `/sensors/data` endpoint
  - [ ] Implement `/bridge/{id}/status` endpoint
  - [ ] Implement `/report/{id}/pdf` endpoint
  - [ ] Add CORS middleware

- [ ] **WebSocket**
  - [ ] Implement WebSocket endpoint
  - [ ] Test connection from React app
  - [ ] Verify data streaming (sensor readings)

- [ ] **Testing**
  - [ ] Test with mock data first
  - [ ] Test with real backend
  - [ ] Test network disconnection handling
  - [ ] Test mobile network (4G/5G)

- [ ] **Error Handling**
  - [ ] Handle connection failures
  - [ ] Show user-friendly error messages
  - [ ] Auto-retry failed requests
  - [ ] Log errors for debugging

---

## 🧪 Testing Endpoints

### Using Postman or curl

```bash
# Test crack detection
curl -X POST http://192.168.1.100:8000/detect \
  -F "image=@test_image.jpg"

# Test sensor data
curl http://192.168.1.100:8000/sensors/data?bridge_id=1

# Test bridge status
curl http://192.168.1.100:8000/bridge/1/status
```

### Using JavaScript Fetch (in browser console)

```javascript
// Test sensor endpoint
fetch('http://192.168.1.100:8000/sensors/data?bridge_id=1')
  .then(r => r.json())
  .then(d => console.log(d));

// Test status endpoint
fetch('http://192.168.1.100:8000/bridge/1/status')
  .then(r => r.json())
  .then(d => console.log(d));
```

---

## 🚨 Common Integration Issues

### Issue 1: CORS Error
```
Access to XMLHttpRequest blocked by CORS policy
```
**Fix**: Add CORS middleware to FastAPI (see section 6️⃣ above)

### Issue 2: WebSocket Connection Refused
```
WebSocket connection to ws://192.168.1.100:8000/ws failed
```
**Fix**: 
- Check backend is running: `python main.py`
- Check firewall isn't blocking port 8000
- Verify correct IP address

### Issue 3: Image Upload 413 Payload Too Large
```
413 Request Entity Too Large
```
**Fix**: In FastAPI, increase max size:
```python
app.add_middleware(
    HTTPMiddleware,
    max_content_length=104857600  # 100MB
)
```

### Issue 4: Sensor Data Not Updating
**Fix**: Check:
- Backend sensor readings are being collected
- WebSocket is sending data regularly
- React component has useEffect dependency array

---

## 📊 Data Format Examples

### Sensor Data JSON
```json
{
  "temperature": 32.5,
  "moisture": 45.2,
  "vibration": 0.82,
  "strain": 125.3,
  "timestamp": "2024-06-20T14:32:00Z"
}
```

### Crack Detection Response
```json
{
  "cracks": [
    {
      "x": 450,
      "y": 320,
      "width": 200,
      "height": 80,
      "confidence": 0.92,
      "severity": 3,
      "crack_type": "structural"
    }
  ]
}
```

### Bridge Status Response
```json
{
  "bridge_name": "Qasr El-Nile Bridge",
  "city": "Cairo",
  "overall_severity": 2,
  "total_cracks": 12,
  "high_severity_cracks": 2,
  "last_inspection_date": "2024-06-20",
  "recommendation": "Monitor Regularly",
  "current_sensors": {
    "temperature": 32,
    "moisture": 45,
    "vibration": 0.8,
    "strain": 120
  }
}
```

---

## 🔑 Key Implementation Points

1. **Keep Mock Data During Development**
   - Develop UI while backend is being built
   - Switch to real API when ready

2. **Use Environment Variables**
   ```javascript
   const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
   ```

3. **Implement Proper Error Handling**
   ```javascript
   try {
     const response = await fetch(url);
     if (!response.ok) throw new Error(`HTTP ${response.status}`);
     return await response.json();
   } catch (error) {
     console.error('API error:', error);
     // Show user-friendly message
   }
   ```

4. **Auto-Retry Failed Requests**
   ```javascript
   async function fetchWithRetry(url, options = {}, retries = 3) {
     for (let i = 0; i < retries; i++) {
       try {
         return await fetch(url, options);
       } catch (error) {
         if (i === retries - 1) throw error;
         await new Promise(r => setTimeout(r, 1000 * (i + 1)));
       }
     }
   }
   ```

---

## 📞 Debugging Tips

1. **Enable DevTools**
   - F12 in browser
   - Network tab shows API requests
   - Console shows errors

2. **Check Backend Logs**
   ```bash
   # Backend should print connection messages
   ✅ Mobile app connected
   📡 Crack detection request received
   ```

3. **Use Browser Network Monitor**
   - F12 → Network tab
   - Filter by XHR/WebSocket
   - See request/response details

4. **Test Offline**
   - DevTools → Network → Offline
   - App should show "Disconnected"

---

## ✅ Integration Complete!

Once all endpoints are implemented and tested:

1. ✅ Real-time sensor data streaming
2. ✅ Photo upload and crack detection
3. ✅ Live dashboard updates
4. ✅ Report generation
5. ✅ Bilingual interface
6. ✅ Mobile responsive
7. ✅ Error handling
8. ✅ Ready for competition!

---

**Questions?** Refer back to:
- README.md for general info
- QUICK_START.md for setup
- This file for integration details

---

*SensorX Challenge 2026 - Bridge Crack Detection System*
