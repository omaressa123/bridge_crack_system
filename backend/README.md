# Bridge Crack Detection Backend

## Overview
This is the FastAPI backend for the Bridge Crack Detection System. It runs on a Raspberry Pi and provides APIs for crack detection, sensor data, and report generation.

## Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database with mock data:
   ```bash
   python init_db.py
   ```

5. Run the server:
   ```bash
   python main.py
   ```

The server will be running at http://localhost:8000

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/ws` | WS | WebSocket for real-time sensor data |
| `/detect` | POST | Detect cracks in uploaded images |
| `/sensors/data` | GET | Get sensor history |
| `/bridge/{id}/status` | GET | Get bridge status |
| `/report/{id}/pdf` | GET | Download PDF report |

## API Documentation
Visit http://localhost:8000/docs for the automatic API documentation.
