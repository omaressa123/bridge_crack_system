from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models import Bridge, CrackDetection, SensorData
from auth import get_current_user
from services.analysis import calculate_overall_severity, get_recommendation
from schemas import BridgeListResponse, BridgeMapResponse, BridgeStatusResponse

router = APIRouter(
    tags=["bridges"],
)


@router.get("/bridges", response_model=BridgeListResponse)
async def get_bridges(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    bridges = db.query(Bridge).all()
    return {"bridges": [{"id": b.id, "name": b.bridge_name, "city": b.city} for b in bridges]}


@router.get("/bridges/map", response_model=BridgeMapResponse)
async def get_bridges_map(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    bridges = db.query(Bridge).all()
    result = []
    for bridge in bridges:
        cracks = db.query(CrackDetection).filter(
            CrackDetection.bridge_id == bridge.id
        ).all()

        max_severity = max((c.severity_level for c in cracks), default=0)
        total_cracks = len(cracks)
        high_severity = sum(1 for c in cracks if c.severity_level >= 3)

        result.append({
            "id": bridge.id,
            "name": bridge.bridge_name,
            "city": bridge.city,
            "latitude": bridge.latitude,
            "longitude": bridge.longitude,
            "max_severity": max_severity,
            "total_cracks": total_cracks,
            "high_severity_cracks": high_severity,
            "recommendation": get_recommendation(max_severity),
        })

    return {"bridges": result}


@router.get("/bridge/{bridge_id}/status", response_model=BridgeStatusResponse)
async def get_bridge_status(
    bridge_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")

    cutoff_time = datetime.utcnow() - timedelta(seconds=30)

    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge_id,
        CrackDetection.detected_at >= cutoff_time,
    ).all()

    # Fall back to all cracks when no recent detections (e.g. seeded demo data)
    if not cracks:
        cracks = db.query(CrackDetection).filter(
            CrackDetection.bridge_id == bridge_id
        ).all()

    latest_sensor = db.query(SensorData).filter(
        SensorData.bridge_id == bridge_id,
        SensorData.timestamp >= cutoff_time,
    ).order_by(SensorData.timestamp.desc()).first()

    if not latest_sensor:
        latest_sensor = db.query(SensorData).filter(
            SensorData.bridge_id == bridge_id
        ).order_by(SensorData.timestamp.desc()).first()

    if not latest_sensor:
        raise HTTPException(status_code=404, detail="No sensor data available for this bridge")

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
            "strain": latest_sensor.strain_gauge_value,
        },
    }
