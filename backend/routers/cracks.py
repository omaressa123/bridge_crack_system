import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from auth import get_current_user
from crack_linking import link_to_previous_crack
from database import get_db
from models import Bridge, CrackDetection, InspectionReport
from schemas import CrackBase, CrackDetectResponse, CrackSaveResponse
from services.crack_history import build_crack_history
from services.notification import send_email_notification, send_sms_notification, send_urgent_notifications
from services.prediction import calculate_crack_growth, detect_cracks_with_yolo, predict_crack_maintenance

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["cracks"],
)


@router.post("/detect", response_model=CrackDetectResponse)
async def detect_cracks(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        contents = await image.read()
        cracks = detect_cracks_with_yolo(contents)
        return {"cracks": cracks}
    except Exception as e:
        logger.exception("Detection error")
        return {"error": str(e), "cracks": []}


@router.post("/detect/{bridge_id}/save", response_model=CrackSaveResponse)
async def save_detections(
    bridge_id: int,
    cracks: List[CrackBase],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
        if not bridge:
            raise HTTPException(status_code=404, detail="Bridge not found")

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
        return {"error": str(e)}


@router.get("/bridge/{bridge_id}/crack-growth")
async def get_crack_growth_history(
    bridge_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")

    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge_id
    ).order_by(CrackDetection.crack_identifier, CrackDetection.detected_at.asc()).all()

    crack_history = {}
    for crack in cracks:
        if crack.crack_identifier not in crack_history:
            crack_history[crack.crack_identifier] = []

        growth = None
        if crack.previous_crack_id:
            previous_crack = (
                db.query(CrackDetection)
                .filter(CrackDetection.id == crack.previous_crack_id)
                .first()
            )
            if previous_crack:
                growth = calculate_crack_growth(crack, previous_crack)

        crack_history[crack.crack_identifier].append({
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
    }


@router.get("/crack/{crack_id}/history")
async def get_crack_history(
    crack_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    history = build_crack_history(crack_id, db)
    if not history:
        raise HTTPException(status_code=404, detail="Crack not found")
    return history


@router.get("/crack/{crack_id}/prediction")
async def get_crack_prediction(
    crack_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    history_resp = build_crack_history(crack_id, db)
    if not history_resp:
        raise HTTPException(status_code=404, detail="Crack not found")

    growth_per_day = history_resp["growth_per_day"] or 0
    return predict_crack_maintenance(history_resp["history"], growth_per_day)
