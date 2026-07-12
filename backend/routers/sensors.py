import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from auth import verify_jwt_token
from database import get_db, SessionLocal
from deps import get_current_active_user
from models import Bridge, SensorData, User
from schemas import SensorDataResponse, SensorTimeRange

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["sensors"],
)

connected_websockets = []

TIME_RANGE_DELTAS = {
    SensorTimeRange.thirty_seconds: timedelta(seconds=30),
    SensorTimeRange.one_hour: timedelta(hours=1),
    SensorTimeRange.twenty_four_hours: timedelta(hours=24),
}


async def broadcast_to_dashboards(payload: dict):
    for ws in list(connected_websockets):
        try:
            await ws.send_json(payload)
        except Exception:
            logger.warning("Removing disconnected websocket client")
            if ws in connected_websockets:
                connected_websockets.remove(ws)


@router.get("/sensors/data", response_model=SensorDataResponse)
async def get_sensor_data(
    bridge_id: int = Query(..., ge=1, description="Bridge ID"),
    limit: int = Query(7, ge=1, le=100),
    time_range: SensorTimeRange = Query(SensorTimeRange.thirty_seconds),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bridge not found")

    cutoff_time = datetime.utcnow() - TIME_RANGE_DELTAS[time_range]

    results = db.query(SensorData).filter(
        SensorData.bridge_id == bridge.id,
        SensorData.timestamp >= cutoff_time,
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
            "timestamps": [],
        }

    return {
        "temperature_history": [r.temperature_c for r in results],
        "moisture_history": [r.moisture_percent for r in results],
        "vibration_history": [r.acceleration_x for r in results],
        "strain_history": [r.strain_gauge_value for r in results],
        "timestamps": [r.timestamp.isoformat() for r in results],
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    if not token:
        await websocket.close(code=1008)
        return
    payload = verify_jwt_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            await websocket.close(code=1008)
            return
    finally:
        db.close()

    await websocket.accept()

    connected_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
