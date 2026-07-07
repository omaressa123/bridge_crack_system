# Bridge Crack Detection System
## Database Design

---

# Database Name

```text
bridge_crack_system
```

---

# Database Architecture

```text
users
│
├── login_history
│
├── notifications
│
└── inspection_reports
        │
        ├── bridges
        │
        ├── crack_detections
        │
        └── sensor_data
```

---

# Tables

## 1. users

Stores all system users authenticated using Google OAuth.

| Column | Type | Description |
|---------|------|-------------|
| id | INT PK | User ID |
| google_id | VARCHAR(100) | Google Account ID |
| full_name | VARCHAR(150) | User Name |
| email | VARCHAR(255) | Gmail Address |
| profile_picture | TEXT | Google Profile Image |
| role | ENUM | User Role |
| is_active | BOOLEAN | Active Account |
| created_at | TIMESTAMP | Registration Date |
| last_login | TIMESTAMP | Last Login |

Roles

- Admin
- Project Manager
- Bridge Engineer
- Inspector
- Viewer

---

## 2. bridges

Stores bridge information.

Current Columns

| Column | Description |
|---------|-------------|
| id | Bridge ID |
| bridge_name | Bridge Name |
| city | City |
| inspection_date | Inspection Date |

Recommended Future Columns

- latitude
- longitude
- bridge_type
- construction_year
- status

---

## 3. inspection_reports

Stores inspection sessions.

Current Columns

| Column | Description |
|---------|-------------|
| id | Report ID |
| bridge_id | Related Bridge |
| report_date | Inspection Date |
| total_cracks_detected | Total Detected Cracks |
| high_severity_cracks | High Severity Count |

Recommended Columns

| Column | Description |
|---------|-------------|
| created_by | User who created the report |
| overall_condition | Bridge Condition |
| recommendation | Maintenance Recommendation |
| inspection_notes | Inspector Notes |
| model_version | YOLO Model Version |
| processing_time | AI Processing Time |

Relationship

```
users
   │
   └──── inspection_reports
```

---

## 4. crack_detections

Stores every crack detected by YOLO.

Current Columns

| Column | Description |
|---------|-------------|
| id | Detection ID |
| bridge_id | Related Bridge |
| x | Bounding Box X |
| y | Bounding Box Y |
| width | Bounding Box Width |
| height | Bounding Box Height |
| area | Crack Area |
| confidence | Detection Confidence |
| severity_level | Severity |
| crack_type | Crack Type |
| crack_identifier | Unique Crack ID |
| previous_crack_id | Previous Detection |
| detected_at | Detection Time |

Recommended Improvement

Instead of only:

```
bridge_id
```

Add

```
report_id
```

Reason

Each bridge can have many inspection reports.

Example

```
Bridge A

Inspection #1

Inspection #2

Inspection #3
```

Each inspection should contain its own detections.

Relationship

```
bridges
    │
inspection_reports
    │
crack_detections
```

instead of

```
bridges
    ├── crack_detections
    └── inspection_reports
```

---

## 5. sensor_data

Stores data received from IoT sensors.

Possible Fields

- temperature
- humidity
- vibration
- tilt
- acceleration
- timestamp

---

## 6. login_history

Stores every login operation.

| Column | Description |
|---------|-------------|
| id | Login ID |
| user_id | User |
| login_time | Login Date |
| ip_address | User IP |
| device_info | Browser / Device |

Purpose

- Security
- Activity Tracking
- Audit

---

## 7. notifications

Stores system notifications.

Example

Critical Crack Detected

Inspection Completed

Bridge Requires Maintenance

Columns

| Column | Description |
|---------|-------------|
| id | Notification ID |
| user_id | Receiver |
| report_id | Related Report |
| title | Notification Title |
| message | Notification Body |
| notification_type | Info / Warning / Critical |
| is_read | Read Status |
| created_at | Creation Date |

Example

```
Title:
Critical Crack Detected

Message:
Bridge Cairo-12 contains a critical crack requiring immediate inspection.
```

---

# Relationships

```
users
│
├── inspection_reports
│         │
│         ├── bridges
│         │
│         ├── crack_detections
│         │
│         └── sensor_data
│
├── login_history
│
└── notifications
```

---

# Authentication Flow

```
User

↓

Sign in with Google

↓

Google OAuth

↓

Flask Backend

↓

Verify ID Token

↓

Check users table

↓

Generate JWT

↓

Frontend stores JWT

↓

Every API Request

Authorization: Bearer <JWT>
```

---

# AI Workflow

```
User Uploads Image

↓

YOLO Detection

↓

Save Detection

↓

Create Inspection Report

↓

Generate Notification (if needed)

↓

Return Results
```

---

# Future Features

- Email Notifications
- Telegram Notifications
- WhatsApp Business API
- Multi-Bridge Dashboard
- GIS Map Integration
- Bridge History Timeline
- Crack Growth Prediction
- Maintenance Scheduling
- Engineer Assignment
- Report Export (PDF)
- Live Sensor Monitoring
- AI Analytics Dashboard

---

# Database Version

Current Version

v1.0

Designed for

Bridge Crack Detection System

Technology Stack

- Flask
- MySQL
- SQLAlchemy
- YOLO
- OpenCV
- Google OAuth
- JWT Authentication