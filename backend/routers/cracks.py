import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session

from deps import get_bridge_or_404, get_current_active_user
from crack_linking import link_to_previous_crack
from database import get_db
from models import Bridge, CrackDetection, InspectionReport
from schemas import (
    CrackBase,
    CrackDetectResponse,
    CrackGrowthResponse,
    CrackHistoryResponse,
    CrackPredictionResponse,
    CrackSaveResponse,
)
from services.crack_history import build_crack_history
from services.notification import send_email_notification, send_sms_notification, send_urgent_notifications
from services.prediction import calculate_crack_growth, detect_cracks_with_yolo, predict_crack_maintenance
from utils.uploads import read_validated_image

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["cracks"],
)


@router.post("/detect", response_model=CrackDetectResponse)
async def detect_cracks(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
):
    try:
        contents = await read_validated_image(image)
        cracks = detect_cracks_with_yolo(contents)
        return {"cracks": cracks}
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.exception("YOLO model not available")
        return {"error": str(e), "cracks": []}
    except Exception as e:
        logger.exception("Detection error")
        return {"error": str(e), "cracks": []}


@router.post("/detect/{bridge_id}/save", response_model=CrackSaveResponse)
async def save_detections(
    cracks: List[CrackBase],
    bridge: Bridge = Depends(get_bridge_or_404),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    if not cracks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one crack is required")

    bridge_id = bridge.id
    try:
        user_id = int(current_user["sub"])
        high_severity_count = len([c for c in cracks if c.severity >= 3])

        report = InspectionReport(
            bridge_id=bridge_id,
            report_date=datetime.utcnow(),
            total_cracks_detected=len(cracks),
            high_severity_cracks=high_severity_count,
            created_by=user_id,
            status="Completed",
        )
        db.add(report)
        db.flush()

        saved_cracks = []
        significant_growth_count = 0

        for crack_data in cracks:
            area = crack_data.width * crack_data.height
            crack = CrackDetection(
                bridge_id=bridge_id,
                x=crack_data.x,
                y=crack_data.y,
                width=crack_data.width,
                height=crack_data.height,
                area=area,
                confidence=crack_data.confidence,
                severity_level=crack_data.severity,
                crack_type=crack_data.crack_type,
                report_id=report.id,
            )
            db.add(crack)
            db.flush()

            link_to_previous_crack(db, bridge_id, crack)

            if crack.previous_crack_id:
                previous_crack = (
                    db.query(CrackDetection)
                    .filter(CrackDetection.id == crack.previous_crack_id)
                    .first()
                )
                if previous_crack:
                    growth = calculate_crack_growth(crack, previous_crack)
                    if growth and growth["grew_significantly"]:
                        significant_growth_count += 1

            saved_cracks.append(crack)

        db.commit()

        send_urgent_notifications(bridge.bridge_name, high_severity_count)
        if significant_growth_count > 0:
            msg = f"{significant_growth_count} cracks showing significant growth!"
            send_email_notification(bridge.bridge_name, msg)
            send_sms_notification(bridge.bridge_name, msg)

        return {
            "message": "Detections saved successfully",
            "report_id": report.id,
            "significant_growth_count": significant_growth_count,
            "saved_crack_ids": [c.id for c in saved_cracks],
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Error saving detections")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/bridge/{bridge_id}/crack-growth", response_model=CrackGrowthResponse)
async def get_crack_growth_history(
    severity_min: Optional[int] = Query(None, ge=1, le=3),
    crack_type: Optional[str] = Query(None, max_length=100),
    bridge: Bridge = Depends(get_bridge_or_404),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    query = db.query(CrackDetection).filter(CrackDetection.bridge_id == bridge.id)
    if severity_min is not None:
        query = query.filter(CrackDetection.severity_level >= severity_min)
    if crack_type:
        query = query.filter(CrackDetection.crack_type.ilike(f"%{crack_type}%"))

    cracks = query.order_by(
        CrackDetection.crack_identifier,
        CrackDetection.detected_at.asc(),
    ).all()

    crack_history: dict[str, list] = {}
    for crack in cracks:
        identifier = crack.crack_identifier or f"unlinked_{crack.id}"
        if identifier not in crack_history:
            crack_history[identifier] = []

        growth = None
        if crack.previous_crack_id:
            previous_crack = (
                db.query(CrackDetection)
                .filter(CrackDetection.id == crack.previous_crack_id)
                .first()
            )
            if previous_crack:
                growth = calculate_crack_growth(crack, previous_crack)

        crack_history[identifier].append({
            "id": crack.id,
            "x": crack.x,
            "y": crack.y,
            "width": crack.width,
            "height": crack.height,
            "area": crack.area,
            "confidence": crack.confidence,
            "severity_level": crack.severity_level,
            "crack_type": crack.crack_type,
            "detected_at": crack.detected_at.isoformat(),
            "growth": growth,
        })

    return {
        "bridge_name": bridge.bridge_name,
        "crack_history": crack_history,
        "total_tracked_cracks": len(crack_history),
    }


@router.get("/crack/{crack_id}/history", response_model=CrackHistoryResponse)
async def get_crack_history(
    crack_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    history = build_crack_history(crack_id, db)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crack not found")
    return history


@router.get("/crack/{crack_id}/prediction", response_model=CrackPredictionResponse)
async def get_crack_prediction(
    crack_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    history_resp = build_crack_history(crack_id, db)
    if not history_resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crack not found")

    growth_per_day = history_resp["growth_per_day"] or 0
    return predict_crack_maintenance(history_resp["history"], growth_per_day)
