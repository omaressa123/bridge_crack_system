# Bridge Crack Detection System

Bilingual (Arabic/English) platform for bridge infrastructure monitoring — from single-image crack detection to **predictive, fleet-level risk management**.

Built for **SensorX Challenge 2026**. Stack: **React (Vite)** frontend + **FastAPI / MySQL** backend, with YOLOv8 crack detection, MQTT sensor ingestion, Google OAuth, and offline-capable deployment on low-cost hardware (e.g. Raspberry Pi).

---

## What it does

| Module | Capability |
|--------|------------|
| **Dashboard** | Bridge status, severity, live sensor snapshot, recommendations |
| **Crack detection** | Upload/capture image → YOLOv8 inference → engineer confirm → save to DB |
| **Crack growth trend** | Track the same physical crack across inspections; area-over-time chart |
| **Predictive maintenance** | Estimate days until critical crack size (linear extrapolation) |
| **Fleet risk map** | Cairo-area bridges on OpenStreetMap, color-coded by severity |
| **Sensor monitoring** | Temperature, moisture, vibration, strain — REST + WebSocket |
| **Inspection reports** | Auto-generated summaries + PDF export |
| **Auth** | Google Sign-In with JWT session |

---

## Architecture

```
┌─────────────────┐     REST / WebSocket      ┌──────────────────────────────┐
│  React Frontend │ ◄──────────────────────► │  FastAPI Backend (backend/)  │
│  (Vite, port    │                           │  • Routers (auth, bridges,   │
│   5173)         │                           │    cracks, reports, sensors) │
└─────────────────┘                           │  • YOLOv8 (yolo_model/)      │
                                              │  • MQTT ingest → MySQL       │
┌─────────────────┐     MQTT                  └──────────────┬───────────────┘
│ fake_sensor_    │ ────────────────────────────────────────►│
│ publisher.py    │   sensors/bridge_N/data                  ▼
└─────────────────┘                                    MySQL database
```

---

## Quick start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **MySQL** 8+
- **Google OAuth** client ID (for login)
- YOLO weights in `yolo_model/best1.pt`

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Linux/macOS

pip install -r requirements.txt
```

Create `backend/.env` (minimum):

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=bridge_crack_db
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
JWT_SECRET=your-long-random-secret
```

Initialize database and demo data, then start the API:

```bash
python init_db.py
python main.py
```

API: **http://localhost:8000** · Docs: **http://localhost:8000/docs**

Full backend setup: [backend/README.md](backend/README.md)

### 2. Frontend

```bash
# From project root
npm install
npm run dev
```

App: **http://localhost:5173**

The frontend reads the API base URL from [api.js](api.js) (`API_URL = http://localhost:8000`). Change it if the backend runs on another host (e.g. Raspberry Pi on the LAN).

### 3. Optional — simulate sensors

```bash
python fake_sensor_publisher.py
```

Requires an MQTT broker on `localhost:1883`. See [docx/README_MQTT_SETUP.md](docx/README_MQTT_SETUP.md).

---

## Demo walkthrough

After seeding (`python init_db.py`):

1. **Log in** with Google OAuth.
2. **Dashboard** — bridge status and sensors for Qasr El-Nile Bridge.
3. **Crack Detection** → **Tracked Cracks** → open **Demo lineage crack** (`CRK-CAIRO12-001`).
   - Growth chart: area over 3 inspections (+437% since first detection).
   - Prediction card: estimated days to critical size + recommended inspection date.
4. **Fleet Map** — 3 Cairo bridges pinned and colored by risk; click markers for details.

Presenter script: [docx/DEMO_TALKING_POINTS.md](docx/DEMO_TALKING_POINTS.md)

---

## Project structure

```
bridge_crack_system/
├── App.jsx                     # Main app shell, auth gate, WebSocket, routing
├── api.js                      # API_URL + authenticatedFetch helper
├── components/
│   ├── BridgeMap.jsx           # Fleet GIS map (Leaflet)
│   ├── CrackDetection.jsx      # Upload, detect, save, tracked cracks panel
│   ├── CrackGrowthChart.jsx    # Growth chart + prediction card
│   ├── Dashboard.jsx
│   ├── Header.jsx
│   ├── InspectionReport.jsx
│   ├── Login.jsx               # Google Sign-In
│   ├── Navigation.jsx          # Bottom tabs incl. Fleet Map
│   └── SensorMonitor.jsx
├── backend/                    # FastAPI application (see backend/README.md)
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── crack_linking.py
│   ├── init_db.py
│   ├── routers/                # auth, bridges, cracks, reports, sensors
│   └── services/               # mqtt, prediction, pdf, notification, analysis
├── yolo_model/
│   └── best1.pt                # YOLOv8 weights
├── fake_sensor_publisher.py    # MQTT test publisher
├── fake_sensors.py / real_sensors.py
├── sensor_config.py
├── docx/                       # Plans, DB docs, MQTT guide, demo script
│   ├── plan.md
│   ├── plan_update.md
│   └── DEMO_TALKING_POINTS.md
├── package.json
└── vite.config.js
```

---

## Frontend scripts

```bash
npm run dev       # Development server (http://localhost:5173)
npm run build     # Production build → dist/
npm run preview   # Preview production build
```

---

## Key API endpoints (summary)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/auth/google` | Login |
| `GET /bridges` | Bridge list |
| `GET /bridges/map` | Fleet map data |
| `GET /bridge/{id}/status` | Dashboard status |
| `POST /detect` | YOLO crack detection |
| `POST /detect/{id}/save` | Save detections + report |
| `GET /crack/{id}/history` | Crack growth timeline |
| `GET /crack/{id}/prediction` | Maintenance window estimate |
| `GET /bridge/{id}/crack-growth` | All tracked cracks on a bridge |
| `GET /sensors/data` | Sensor history |
| `WS /ws?token=` | Live sensor stream |
| `GET /report/{id}/pdf` | PDF download |

Full table with auth requirements: [backend/README.md](backend/README.md)

---

## Bilingual support

- Full **English / Arabic** UI with RTL layout for Arabic
- Language toggle in the header
- Prediction messages returned in both languages from the API

---

## Documentation

| Document | Contents |
|----------|----------|
| [backend/README.md](backend/README.md) | Backend setup, env vars, full API reference |
| [docx/plan.md](docx/plan.md) | Original enhancement plan (3 features) |
| [docx/plan_update.md](docx/plan_update.md) | Feature completion status |
| [docx/DEMO_TALKING_POINTS.md](docx/DEMO_TALKING_POINTS.md) | Judge demo script |
| [docx/DATABASE.md](docx/DATABASE.md) | Database schema |
| [docx/README_MQTT_SETUP.md](docx/README_MQTT_SETUP.md) | MQTT broker + sensor simulation |

---

## Honest scope notes (for demos / judges)

- **Prediction** is linear trend extrapolation from historical detections — not a trained ML forecasting model.
- **Growth demo data** is backdated seed data (`CRK-CAIRO12-001`) simulating weeks of field inspections.
- **Crack linking** uses bounding-box proximity on the same bridge — MVP approach; production v2 would add visual re-identification.

---

## License

SensorX Challenge 2026 — all rights reserved.

**Version:** 2.0.0  
**Last updated:** July 2026
