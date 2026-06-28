# Bridge Crack Detection Mobile App - React

## 🏗️ Project Overview

Bilingual (Arabic/English) mobile application for real-time bridge infrastructure crack detection and sensor monitoring. Built with React, supports image upload, live sensor data visualization, and inspection report generation.

---

## ✨ Features

### 📊 Dashboard
- Overall bridge status and severity level
- Live sensor data (temperature, moisture, vibration, strain)
- Recent activity feed
- Quick statistics (crack count, high-severity cracks)

### 🔍 Crack Detection
- Photo upload (from device or camera)
- Real-time crack detection with YOLOv8 model
- Confidence scores and severity levels
- Engineer confirmation/rejection workflow
- Crack coordinate mapping

### 📡 Sensor Monitoring
- Real-time sensor data visualization
- Time-series charts (temperature, moisture, vibration, strain)
- Anomaly detection alerts
- Historical data analysis
- Customizable time ranges (1h, 6h, 24h, 7d)

### 📋 Inspection Reports
- Auto-generated inspection reports
- PDF export and sharing
- Engineer notes and recommendations
- Historical report archive
- Quick report generation

### 🌍 Bilingual Support
- Full Arabic/English support
- RTL (Right-to-Left) layout for Arabic
- Seamless language switching
- All UI elements translated

---

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ (download from https://nodejs.org/)
- npm or yarn package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Navigate to project directory**
```bash
cd bridge-crack-app
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The app will open automatically at `http://localhost:5173`

---

## 📁 Project Structure

```
bridge-crack-app/
├── components/
│   ├── Header.jsx              # App header with language toggle
│   ├── Navigation.jsx          # Bottom navigation tabs
│   ├── Dashboard.jsx           # Overview and status
│   ├── CrackDetection.jsx      # Photo upload & detection
│   ├── SensorMonitor.jsx       # Real-time sensor data
│   └── InspectionReport.jsx    # Report management
├── App.jsx                     # Main app component
├── App.css                     # Global styles (fully styled)
├── main.jsx                    # React entry point
├── index.html                  # HTML template
├── vite.config.js              # Vite configuration
└── package.json                # Dependencies

```

---

## 🔧 Configuration

### WebSocket Connection
Edit the WebSocket URL in `App.jsx` (line ~26):

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
// Change 'localhost:8000' to your Raspberry Pi IP:PORT
// Example: ws://192.168.1.100:8000/ws
```

### API Endpoints
Update API calls in components to match your backend:

**In CrackDetection.jsx:**
```javascript
// Replace with your actual backend URL
const response = await fetch('http://your-rpi-ip:8000/detect', {
  method: 'POST',
  body: formData
});
```

**In SensorMonitor.jsx:**
```javascript
// Fetch sensor data from your backend
const data = await fetch('http://your-rpi-ip:8000/sensors/data?bridge_id=1');
```

---

## 💻 Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code (setup eslint first)
npm run lint
```

### File Structure for New Components

```jsx
// Template for new components
import React, { useState, useEffect } from 'react';

export default function NewComponent({ language, t, bridgeId }) {
  const [data, setData] = useState(null);

  const translations = {
    en: { /* English translations */ },
    ar: { /* Arabic translations */ }
  };

  const trans = translations[language];

  return (
    <div className="new-component">
      {/* Your JSX here */}
    </div>
  );
}
```

---

## 🎨 Styling Guide

### CSS Variables
All colors and spacing use CSS variables defined in `App.css`:

```css
:root {
  --primary-color: #1F4E78;      /* Main blue */
  --secondary-color: #4472C4;    /* Accent blue */
  --success-color: #10B981;      /* Green */
  --warning-color: #F59E0B;      /* Orange */
  --danger-color: #EF4444;       /* Red */
  --light-bg: #F5F7FA;           /* Light gray background */
  --border-color: #E5E7EB;       /* Light border */
  --text-primary: #1F2937;       /* Dark text */
  --text-secondary: #6B7280;     /* Gray text */
}
```

### Responsive Design
- **Mobile**: < 480px
- **Tablet**: 480px - 768px
- **Desktop**: > 768px

All components are fully responsive with media queries in `App.css`.

---

## 🌐 Bilingual Implementation

### Language Switching
```jsx
// In parent component
const [language, setLanguage] = useState('en'); // 'en' or 'ar'

// Pass to children
<ChildComponent language={language} t={translations[language]} />
```

### RTL Support
```css
.app.rtl {
  direction: rtl;
  text-align: right;
}

.app.ltr {
  direction: ltr;
  text-align: left;
}
```

### Translation Object Format
```javascript
const translations = {
  en: {
    key: 'English text',
    anotherKey: 'More text',
  },
  ar: {
    key: 'النص العربي',
    anotherKey: 'المزيد من النص',
  }
};
```

---

## 📱 Mobile Optimization

### Viewport Meta Tag
Already set in `index.html`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
```

### Touch-Friendly Design
- Buttons: 44px+ tap targets
- Spacing: 10-20px gaps
- Font sizes: 14px+ for readability

### PWA Features (Optional Setup)
To make it installable on mobile:

1. Add `manifest.json`:
```json
{
  "name": "Bridge Crack Detection",
  "short_name": "Bridge Cracks",
  "icons": [...],
  "theme_color": "#1F4E78",
  "background_color": "#ffffff",
  "display": "standalone"
}
```

2. Reference in `index.html`:
```html
<link rel="manifest" href="/manifest.json">
```

---

## 🔌 Backend Integration

### Expected API Responses

**POST /detect** - Crack Detection
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
      "type": "structural"
    }
  ]
}
```

**GET /sensors/data** - Sensor Readings
```json
{
  "temperature": 32,
  "moisture": 45,
  "vibration": 0.8,
  "strain": 120,
  "timestamp": "2024-06-20T14:30:00Z"
}
```

**GET /severity** - Overall Status
```json
{
  "score": 65,
  "level": "monitor",
  "cracks_count": 12,
  "high_severity": 2
}
```

---

## 🚢 Deployment

### Build for Production
```bash
npm run build
```

This creates an optimized `dist/` folder.

### Deploy Options

#### Option 1: GitHub Pages
```bash
npm install gh-pages --save-dev
# Add to package.json:
# "homepage": "https://yourusername.github.io/bridge-crack-app"
# "deploy": "npm run build && gh-pages -d dist"
npm run deploy
```

#### Option 2: Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

#### Option 3: Self-Hosted
```bash
# Copy dist/ to your web server
scp -r dist/* user@server:/var/www/html/
```

#### Option 4: Docker
```dockerfile
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] English UI loads correctly
- [ ] Arabic UI displays RTL properly
- [ ] Language toggle switches seamlessly
- [ ] Image upload works
- [ ] Crack detection results display correctly
- [ ] Sensor charts update in real-time
- [ ] Reports generate and export as PDF
- [ ] Mobile responsive on all screen sizes
- [ ] WebSocket connection to RPi works
- [ ] No console errors

### Browser Compatibility
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile Safari (iOS 12+)
- ✅ Chrome Mobile (Android 5+)

---

## 🐛 Troubleshooting

### WebSocket Connection Fails
```
Error: WebSocket is closed before the connection is established
```
**Solution**: Ensure Raspberry Pi backend is running on correct IP:PORT

### Images Not Uploading
- Check file size (should be < 5MB)
- Verify backend has `/upload` endpoint
- Check CORS headers

### RTL Text Overlapping
- Ensure `.app.rtl` class is applied
- Check font supports Arabic characters
- Verify CSS direction property

### Performance Issues
- Run `npm run build` and check bundle size
- Use React DevTools Profiler
- Check for unnecessary re-renders

---

## 📚 Additional Resources

### Documentation
- [React Documentation](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [CSS Grid Tutorial](https://css-tricks.com/snippets/css/complete-guide-grid/)

### Related Files
- Excel Plan: `Bridge_Crack_Detection_SensorX_Plan.xlsx`
- Team Plan: `bridge_crack_team_plan.md`
- Backend API: See `components/` for endpoint usage

---

## 📞 Support & Feedback

For issues or suggestions:
1. Check troubleshooting section
2. Review component documentation
3. Check browser console for errors
4. Verify WebSocket/API connections

---

## 📄 License

This project is part of SensorX Challenge 2026. All rights reserved.

---

## 🎯 Next Steps

1. **Connect to Real Backend**
   - Update WebSocket URL to your Raspberry Pi IP
   - Implement actual API calls instead of mock data

2. **Add Authentication**
   - Engineer login system
   - Role-based access control

3. **Implement PDF Export**
   - Use `jspdf` library for report generation
   - Add chart snapshots to PDFs

4. **Database Integration**
   - Sync local app data with backend database
   - Historical data caching

5. **Offline Support**
   - Service Worker for PWA
   - LocalStorage for offline functionality

6. **Camera Integration**
   - Real camera access on mobile
   - Image compression before upload

---

**Version**: 1.0.0  
**Last Updated**: June 2024  
**Built for**: SensorX Challenge 2026
