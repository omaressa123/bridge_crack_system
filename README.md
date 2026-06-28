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
- Python 3.8+ for backend
- MySQL database for backend

### Installation

#### Backend Setup
1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create a virtual environment (optional but recommended)**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create .env file**
```bash
cp .env.example .env
```
Then edit the .env file with your MySQL credentials.

5. **Initialize database (optional: add mock data)**
```bash
python init_db.py
```

6. **Start backend server**
```bash
python main.py
```
Backend will be available at `http://localhost:8000`

#### Frontend Setup
1. **Navigate to project root directory**
```bash
cd ..
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
│   ├── Header.jsx              # App header with language toggle and bridge selector
│   ├── Navigation.jsx          # Bottom navigation tabs
│   ├── Dashboard.jsx           # Overview and status
│   ├── CrackDetection.jsx      # Photo upload & detection
│   ├── SensorMonitor.jsx       # Real-time sensor data
│   └── InspectionReport.jsx    # Report management
├── backend/
│   ├── main.py                 # FastAPI main backend app
│   ├── models.py               # SQLAlchemy models
│   ├── init_db.py              # Database initialization with mock data
│   ├── requirements.txt        # Python dependencies
│   ├── rdd.yaml                # YOLO model configuration
│   └── .env.example            # Environment variables template
├── yolo_model/                 # YOLO model weights
│   ├── best1.pt                # Best trained model
│   ├── last.pt                 # Last checkpoint
│   └── results 2.png           # Training results
├── App.jsx                     # Main app component
├── App.css                     # Global styles (fully styled)
├── main.jsx                    # React entry point
├── index.html                  # HTML template
├── vite.config.js              # Vite configuration
├── package.json                # Dependencies
└── .gitignore                  # Git ignore file
```

---

## 🔧 Configuration

### API_URL Configuration
All frontend components use an API_URL constant. You can change it in each component or make a global config file.

### Environment Variables for Backend
Create a .env file in backend/ directory:
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=bridge_crack_db
```

---

## 💻 Development

### Available Scripts (Frontend)

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

---

## 🌐 Bilingual Implementation

### Language Switching
```jsx
// In parent component
const [language, setLanguage] = useState('en'); // 'en' or 'ar'

// Pass to children
<ChildComponent language={language} t={translations[language]} />
```

---

##  Deployment

### Build for Production (Frontend)
```bash
npm run build
```
This creates an optimized `dist/` folder.

---

## 📄 License

This project is part of SensorX Challenge 2026. All rights reserved.

---

**Version**: 1.0.0  
**Last Updated**: June 2024  
**Built for**: SensorX Challenge 2026
