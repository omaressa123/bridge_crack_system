from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from deps import get_bridge_or_404, get_current_active_user
from models import Bridge, CrackDetection, SensorData
from schemas import BridgeListResponse, BridgeMapResponse, BridgeStatusResponse
from services.analysis import calculate_overall_severity, get_recommendation
from services.bridge_stats import get_bridge_crack_stats

router = APIRouter(
    tags=["bridges"],
)


@router.get("/bridges", response_model=BridgeListResponse)
async def get_bridges(
    city: Optional[str] = Query(None, description="Filter bridges by city"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    query = db.query(Bridge)
    if city:
        query = query.filter(Bridge.city.ilike(f"%{city}%"))
    bridges = query.order_by(Bridge.bridge_name.asc()).all()
    return {"bridges": [{"id": b.id, "name": b.bridge_name, "city": b.city} for b in bridges]}


@router.get("/bridges/map", response_model=BridgeMapResponse)
async def get_bridges_map(
    city: Optional[str] = Query(None, description="Filter bridges by city"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    query = db.query(Bridge)
    if city:
        query = query.filter(Bridge.city.ilike(f"%{city}%"))
    bridges = query.order_by(Bridge.bridge_name.asc()).all()

    bridge_ids = [b.id for b in bridges]
    stats_by_bridge = get_bridge_crack_stats(db, bridge_ids)

    result = []
    for bridge in bridges:
        stats = stats_by_bridge.get(bridge.id, {
            "max_severity": 0,
            "total_cracks": 0,
            "high_severity_cracks": 0,
        })
        max_severity = stats["max_severity"]
        result.append({
            "id": bridge.id,
            "name": bridge.bridge_name,
            "city": bridge.city,
            "latitude": bridge.latitude,
            "longitude": bridge.longitude,
            "max_severity": max_severity,
            "total_cracks": stats["total_cracks"],
            "high_severity_cracks": stats["high_severity_cracks"],
            "recommendation": get_recommendation(max_severity),
        })

    return {"bridges": result}


@router.get("/bridge/{bridge_id}/status", response_model=BridgeStatusResponse)
async def get_bridge_status(
    bridge: Bridge = Depends(get_bridge_or_404),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    cutoff_time = datetime.utcnow() - timedelta(seconds=30)

    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge.id,
        CrackDetection.detected_at >= cutoff_time,
    ).all()

    if not cracks:
        cracks = db.query(CrackDetection).filter(
            CrackDetection.bridge_id == bridge.id
        ).all()

    latest_sensor = db.query(SensorData).filter(
        SensorData.bridge_id == bridge.id,
        SensorData.timestamp >= cutoff_time,
    ).order_by(SensorData.timestamp.desc()).first()

    if not latest_sensor:
        latest_sensor = db.query(SensorData).filter(
            SensorData.bridge_id == bridge.id
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
