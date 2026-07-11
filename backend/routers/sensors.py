from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from models import SensorData
from auth import verify_jwt_token

router = APIRouter(
    tags=["sensors"],
)

# Shared state for WebSockets (for broadcast)
connected_websockets = []

async def broadcast_to_dashboards(payload: dict):
    for ws in list(connected_websockets):
        try:
            await ws.send_json(payload)
        except Exception:
            if ws in connected_websockets:
                connected_websockets.remove(ws)

@router.get("/sensors/data")
async def get_sensor_data(bridge_id: int, limit: int = 7, time_range: str = "30s", db: Session = Depends(get_db)):
    if time_range == "30s":
        cutoff_time = datetime.utcnow() - timedelta(seconds=30)
    elif time_range == "1h":
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
    elif time_range == "24h":
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
    else:
        cutoff_time = datetime.utcnow() - timedelta(seconds=30)
    
    results = db.query(SensorData).filter(
        SensorData.bridge_id == bridge_id,
        SensorData.timestamp >= cutoff_time
    ).order_by(
        SensorData.timestamp.desc()
    ).limit(limit).all()
    results = list(reversed(results))
    
    if not results:
        return {
            "temperature_history": [],
            "moisture_history": [],
            "vibration_history": [],
            "strain_history": [],
            "timestamps": []
        }
    
    return {
        "temperature_history": [r.temperature_c for r in results],
        "moisture_history": [r.moisture_percent for r in results],
        "vibration_history": [r.acceleration_x for r in results],
        "strain_history": [r.strain_gauge_value for r in results],
        "timestamps": [r.timestamp.isoformat() for r in results]
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    await websocket.accept()
    if not token:
        await websocket.close(code=1008)
        return
    payload = verify_jwt_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    
    connected_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
