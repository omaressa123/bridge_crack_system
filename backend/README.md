# Bridge Crack Detection — Backend

FastAPI + SQLAlchemy + MySQL backend for the Bridge Crack Detection System. Provides crack detection (YOLOv8), sensor ingestion (MQTT), inspection reports, Google OAuth login, crack growth tracking, predictive maintenance estimates, and a multi-bridge GIS map API.

Designed to run on a Raspberry Pi or any Linux host with offline-capable inference.

**API docs (auto-generated):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Features

| Area | Description |
|------|-------------|
| **Crack detection** | YOLOv8 inference on uploaded images (`POST /detect`) |
| **Crack growth trend** | Links repeat detections via bounding-box proximity; timeline API per crack |
| **Predictive maintenance** | Linear extrapolation of crack area to estimate days until critical size |
| **Multi-bridge map** | Fleet endpoint with lat/lng, severity, and crack counts per bridge |
| **Sensor monitoring** | MQTT ingestion + REST history + WebSocket broadcast |
| **Inspection reports** | PDF generation for saved inspection runs |
| **Authentication** | Google Sign-In → project JWT (Bearer token on protected routes) |
| **Notifications** | Optional email (SMTP) and SMS (Twilio) on high-severity saves |

---

## Prerequisites

- Python 3.10+
- MySQL 8+ (or MariaDB with compatible driver)
- YOLO weights at `yolo_model/best1.pt` (relative to project root)
- Optional: MQTT broker on `localhost:1883` for live sensor data
- Optional: Google OAuth client ID for login

---

## Quick start

```bash
cd backend

# 1. Virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (create backend/.env — see below)

# 4. Create tables + seed demo data (3 Cairo bridges, crack lineage CRK-CAIRO12-001)
python init_db.py

# 5. Run the server
python main.py
```

Server: **http://localhost:8000**

Interactive API reference: **http://localhost:8000/docs**

---

## Environment variables

Create a `backend/.env` file:

```env
# MySQL (required)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=bridge_crack_db

# Google OAuth + JWT (required for login)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
JWT_SECRET=change-this-to-a-long-random-secret

# Email notifications (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_smtp_password
NOTIFICATION_EMAIL_TO=engineer@example.com

# SMS notifications (optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
NOTIFICATION_SMS_TO=

```

MQTT broker host/port are currently set in `services/mqtt.py` (`localhost:1883`). Topic pattern: `sensors/{bridge_id}/data`.

---

## Database & seed data

`init_db.py` does two things:

1. Creates all tables via SQLAlchemy (`database.init_db`)
2. Seeds demo data:
   - **3 Cairo bridges** with GIS coordinates (Qasr El-Nile, 6th October, Imbaba)
   - **Sensor history** for the primary bridge
   - **Crack lineage** `CRK-CAIRO12-001` — 3 backdated inspections over 21 days (for growth/prediction demo)
   - Sample cracks on all bridges + one inspection report

Re-running on a non-empty database may duplicate rows. For a clean slate, drop and recreate `bridge_crack_db` in MySQL first.

See also: [docx/DATABASE.md](../docx/DATABASE.md)

---

## API endpoints

Most routes require `Authorization: Bearer <jwt>`. Exceptions noted below.

### Health & auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | No | Health check |
| `POST` | `/api/auth/google` | No | Google Sign-In; returns JWT + user profile |

### Bridges

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/bridges` | Yes | List all bridges |
| `GET` | `/bridges/map` | Yes | Fleet map data (lat/lng, severity, crack counts) |
| `GET` | `/bridge/{bridge_id}/status` | Yes | Live status + recent cracks + latest sensors |

### Cracks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/detect` | Yes | Detect cracks in uploaded image (multipart `image`) |
| `POST` | `/detect/{bridge_id}/save` | Yes | Persist detections + create inspection report |
| `GET` | `/bridge/{bridge_id}/crack-growth` | Yes | All crack lineages grouped by `crack_identifier` |
| `GET` | `/crack/{crack_id}/history` | Yes | Timeline walking `previous_crack_id` chain |
| `GET` | `/crack/{crack_id}/prediction` | Yes | Linear maintenance window estimate (bilingual) |

### Reports

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/bridge/{bridge_id}/reports` | Yes | List inspection reports for a bridge |
| `GET` | `/report/{report_id}/pdf` | Yes | Download PDF report |

### Sensors

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sensors/data?bridge_id=&limit=&time_range=` | No | Sensor history (`time_range`: `30s`, `1h`, `24h`) |
| `WS` | `/ws?token=` | JWT in query | Real-time sensor broadcast (MQTT → WebSocket) |

---

## Project structure

```
backend/
├── main.py                 # FastAPI app, CORS, router registration, startup (DB + MQTT)
├── database.py             # MySQL engine, SessionLocal, Base, get_db, init_db
├── models.py               # Bridge, CrackDetection, SensorData, InspectionReport, User
├── schemas.py              # Pydantic request/response models
├── auth.py                 # Google token verify, JWT create/verify, get_current_user
├── crack_linking.py        # link_to_previous_crack() — bbox proximity matching
├── init_db.py              # Create tables + seed demo data
├── requirements.txt
├── routers/
│   ├── auth.py             # /api/auth/google
│   ├── bridges.py          # /bridges, /bridges/map, /bridge/{id}/status
│   ├── cracks.py           # /detect, history, prediction, crack-growth
│   ├── reports.py          # Reports list + PDF
│   └── sensors.py          # /sensors/data, /ws
└── services/
    ├── analysis.py         # Severity scoring + recommendations
    ├── mqtt.py             # MQTT listener → DB + WebSocket broadcast
    ├── notification.py     # Email + SMS alerts
    ├── pdf.py              # ReportLab PDF generation
    └── prediction.py       # YOLO inference, growth calc, maintenance prediction
```

YOLO weights live outside this folder: `../yolo_model/best1.pt`

---

## MQTT sensor simulation

To simulate hardware sensors before deployment:

```bash
# From project root — publishes to sensors/bridge_1/data, etc.
python fake_sensor_publisher.py
```

The backend MQTT listener starts automatically with the API server and writes readings to `sensor_data`, then broadcasts to connected WebSocket clients.

More detail: [docx/README_MQTT_SETUP.md](../docx/README_MQTT_SETUP.md)

---

## Demo verification

After `python init_db.py` and starting the server:

1. Log in via the frontend (Google OAuth).
2. Select **Qasr El-Nile Bridge**.
3. Open **Crack Detection** → **Tracked Cracks** → **Demo lineage crack** → growth chart + prediction card.
4. Open **Fleet Map** → 3 Cairo bridges on the map.

Judge demo script: [docx/DEMO_TALKING_POINTS.md](../docx/DEMO_TALKING_POINTS.md)

---

## Development notes

- Run commands from the `backend/` directory so Python imports resolve correctly.
- Prediction uses **linear trend extrapolation**, not a trained forecasting model.
- Crack linking uses **bounding-box center proximity** (40 px threshold) — suitable for MVP/demo.
- High-severity notifications are skipped silently if SMTP/Twilio env vars are missing.

**Version:** 2.0.0  
**Challenge:** SensorX Challenge 2026
