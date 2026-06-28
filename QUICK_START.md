# 🚀 QUICK START GUIDE - Bridge Crack Detection React App

## ⚡ 3-Minute Setup

### Step 1: Install Node.js (if not already installed)
Download from: https://nodejs.org/
- Choose LTS (Long Term Support) version
- Install and verify:
```bash
node --version    # Should show v16+ 
npm --version     # Should show 8+
```

### Step 2: Extract & Navigate
```bash
# Extract the bridge-crack-app folder
cd bridge-crack-app
```

### Step 3: Install Dependencies
```bash
npm install
# This downloads all required packages (~200MB)
# Wait 2-3 minutes...
```

### Step 4: Start the App
```bash
npm run dev
```

Browser will automatically open at: `http://localhost:5173`

---

## 🎮 Testing the App (Without Backend)

The app comes with **mock data** so you can test everything without a Raspberry Pi:

### ✅ What Works Out of the Box:
- ✅ Dashboard view with sample data
- ✅ Language toggle (English ↔ Arabic)
- ✅ RTL layout for Arabic
- ✅ Image upload simulation
- ✅ Crack detection results visualization
- ✅ Sensor charts and graphs
- ✅ Inspection report generation
- ✅ Mobile responsive design

### 🔧 To Use Real Backend Later:
Edit `App.jsx` (line 26):
```javascript
// Change this:
const ws = new WebSocket('ws://localhost:8000/ws');

// To your Raspberry Pi IP:
const ws = new WebSocket('ws://192.168.1.100:8000/ws');
```

---

## 📂 Project Files

```
bridge-crack-app/
├── App.jsx                          ← Main app (bilingual logic)
├── App.css                          ← All styling (1000+ lines)
├── main.jsx                         ← React entry point
├── index.html                       ← HTML template
├── package.json                     ← Dependencies list
├── vite.config.js                   ← Build config
├── README.md                        ← Full documentation
│
└── components/                      ← 6 React components
    ├── Header.jsx                   (App title, language toggle)
    ├── Navigation.jsx               (Bottom tabs)
    ├── Dashboard.jsx                (Overview, status, sensors)
    ├── CrackDetection.jsx           (Photo upload, detection)
    ├── SensorMonitor.jsx            (Live charts)
    └── InspectionReport.jsx         (Report management)
```

---

## 🌍 Bilingual Features

### English/Arabic Toggle
Click the language button in top-right corner (عربي/English)

### Automatic Features:
- Text switches immediately
- Layout flips (LTR ↔ RTL)
- All components responsive to RTL
- Arabic numerals & labels

### Translation Example:
```javascript
// In each component:
const translations = {
  en: { dashboard: 'Dashboard' },
  ar: { dashboard: 'لوحة التحكم' }
};
```

---

## 📱 Mobile Testing

### Chrome DevTools Method:
1. Open app in Chrome
2. Press `F12` (open DevTools)
3. Click device icon (📱) in top-left
4. Select mobile device (iPhone 12, Pixel 5, etc.)
5. Refresh page

### Phone Method:
1. Find your computer IP: 
   - Windows: `ipconfig` → IPv4 Address
   - Mac/Linux: `ifconfig` → inet address
   
2. On phone, visit: `http://YOUR_IP:5173`

---

## 🔧 Customization Guide

### Change Colors
Edit `:root` in `App.css` (lines 12-24):
```css
:root {
  --primary-color: #1F4E78;    ← Change this
  --secondary-color: #4472C4;
  --success-color: #10B981;
  --warning-color: #F59E0B;
  --danger-color: #EF4444;
}
```

### Change App Title
Edit `App.jsx` translations (line 25):
```javascript
appTitle: 'Bridge Crack Detection System'  // Change here
```

### Add New Component
1. Create `components/MyComponent.jsx`
2. Copy template from Dashboard.jsx
3. Import in App.jsx:
```javascript
import MyComponent from './components/MyComponent';
```
4. Add to render:
```jsx
{currentTab === 'mycomponent' && (
  <MyComponent language={language} t={t} bridgeId={bridgeId} />
)}
```

---

## 🐛 Common Issues & Fixes

### Issue: "npm command not found"
**Solution**: Node.js not installed properly
- Download from: https://nodejs.org/
- Restart computer after installing
- Verify: `node --version`

### Issue: Port 5173 already in use
**Solution**: Change port in vite.config.js:
```javascript
server: {
  port: 5174,  // ← Change to different port
}
```

### Issue: "CORS error" when connecting to backend
**Solution**: Backend needs CORS headers. In your FastAPI code:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Image upload not working
**Solution**: Backend needs `/upload` endpoint. In FastAPI:
```python
@app.post("/upload")
async def upload_image(file: UploadFile):
    # Handle image upload
    return {"filename": file.filename}
```

---

## 📊 Features Explained

### 1. Dashboard Tab 📊
Shows:
- Overall bridge condition (Safe/Monitor/Urgent)
- Live sensor readings
- Crack statistics
- Recent activity

Mock data: Updates every 5 seconds

### 2. Crack Detection Tab 🔍
Does:
- Upload photos from device
- Display detected cracks with confidence scores
- Show severity levels
- Confirm/reject detections

Mock data: 3 sample cracks with 87-92% confidence

### 3. Sensors Tab 📡
Shows:
- Temperature (°C)
- Moisture (%)
- Vibration (g)
- Strain (μ)

All with live charts. Toggle time range (1h/6h/24h/7d)

### 4. Report Tab 📋
Includes:
- Past inspection reports
- Generate new reports
- Download as PDF
- Share via email/WhatsApp/SMS
- View detailed report

---

## 🎯 Integration Checklist

When ready to connect real backend:

- [ ] Update WebSocket URL in App.jsx
- [ ] Create `/detect` endpoint for crack detection
- [ ] Create `/sensors/data` endpoint for sensor readings
- [ ] Create `/severity` endpoint for overall status
- [ ] Create `/report/generate` endpoint for PDF
- [ ] Add CORS headers to FastAPI backend
- [ ] Test endpoints with Postman first
- [ ] Update mock data calls to real API calls

---

## 📚 File Reference

### App.jsx (Main Component)
- Lines 1-30: Imports & WebSocket setup
- Lines 32-50: Translations object
- Lines 52-100: Main JSX render

### Components
| File | Purpose | Lines |
|------|---------|-------|
| Header.jsx | Title + language toggle | ~30 |
| Dashboard.jsx | Overview + stats | ~180 |
| CrackDetection.jsx | Photo upload + detection | ~220 |
| SensorMonitor.jsx | Live sensor charts | ~250 |
| InspectionReport.jsx | Report management | ~300 |

### App.css
- Lines 1-100: Global styles
- Lines 100-300: Components
- Lines 300-500: Cards & cards
- Lines 500-700: Forms & buttons
- Lines 700-900: Modal & nav
- Lines 900-1000: Responsive

---

## 🚀 Next: Connect to Raspberry Pi

### 1. Get Your Pi's IP Address
```bash
# On Raspberry Pi:
hostname -I
# Example output: 192.168.1.100
```

### 2. Update WebSocket URL
In `App.jsx` line 26:
```javascript
const ws = new WebSocket('ws://192.168.1.100:8000/ws');
```

### 3. Test Connection
Open browser console (F12) and look for:
```
✅ Connected to Raspberry Pi
```

---

## 💡 Pro Tips

### Tip 1: Debug Mode
Open browser DevTools (F12) to see:
- Console logs
- Network requests
- React component state
- WebSocket messages

### Tip 2: Save Development Time
Mock data is pre-configured so you can develop UI while backend is being built.

### Tip 3: Hot Reload
Edit any file and save → App reloads automatically!
No need to restart server.

### Tip 4: Mobile Testing
Use Chrome DevTools mobile emulation to catch responsive issues early.

---

## 🎬 Demo Script (For Judging)

When presenting at competition:

1. **Show Dashboard**
   - Click "📊 Dashboard"
   - Point out sensor readings in real-time
   - Toggle language to show bilingual

2. **Show Crack Detection**
   - Click "🔍 Crack Detection"
   - Click "📁 Select Image from Device"
   - Click "🔍 Detect Cracks"
   - Show confidence scores

3. **Show Sensor Monitoring**
   - Click "📡 Sensors"
   - Toggle time range (1h/6h/24h/7d)
   - Explain anomaly alerts

4. **Show Reports**
   - Click "📋 Report"
   - Click on a report card
   - Show PDF download option

5. **Show Bilingual**
   - Click language button in header
   - Show Arabic RTL layout
   - Explain translation system

**Total time: ~3 minutes**

---

## 📞 Quick Help

### Problem? Try These:
1. Check browser console (F12)
2. Verify port 5173 is not blocked
3. Clear browser cache (Ctrl+Shift+Delete)
4. Restart `npm run dev`
5. Check README.md for more details

### Still stuck?
Review the main README.md file in the project folder for comprehensive troubleshooting.

---

## ✅ Launch Checklist

Before showing to judges:

- [ ] App starts without errors
- [ ] All 4 tabs work
- [ ] English/Arabic toggle works
- [ ] Mobile layout responsive
- [ ] Console has no red errors
- [ ] Images load
- [ ] Charts render
- [ ] Browser DevTools open (F12) for debugging

---

## 📦 What's Included

✅ Complete React app (6 components)
✅ Bilingual (Arabic/English)
✅ Mobile responsive
✅ Mock sensor data
✅ Sample crack detection
✅ 1000+ lines of CSS
✅ Fully styled UI
✅ Ready-to-use charts
✅ Report generation UI
✅ WebSocket integration ready

---

## 🎓 Learning Resources

While developing, learn from:
1. **App.jsx**: Component structure
2. **App.css**: Responsive design
3. **components/**: How to build features
4. **README.md**: Full documentation

---

**Good luck with your presentation! 🚀**

Questions? Check README.md for detailed documentation.

---

*Built for SensorX Challenge 2026*
*Last Updated: June 2024*
