from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Bridge, CrackDetection, InspectionReport
from auth import get_current_user
from services.prediction import detect_cracks_with_yolo, calculate_crack_growth, predict_crack_maintenance
from services.crack_linking import link_to_previous_crack
from services.notification import send_urgent_notifications, send_email_notification, send_sms_notification

router = APIRouter(
    tags=["cracks"],
)

@router.post("/detect")
async def detect_cracks(image: UploadFile = File(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        contents = await image.read()
        cracks = detect_cracks_with_yolo(contents)
        return {"cracks": cracks}
    except Exception as e:
        print(f"Detection error: {str(e)}")
        return {"error": str(e), "cracks": []}

@router.post("/detect/{bridge_id}/save")
async def save_detections(bridge_id: int, cracks: list[dict], db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
        if not bridge:
            return {"error": "Bridge not found"}
        
        saved_cracks = []
        significant_growth_count = 0
        
        for crack_data in cracks:
            area = crack_data["width"] * crack_data["height"]
            
            # Simple identifier based on bucketed position if not already provided
            # In the original main.py, generate_crack_identifier was used here.
            # I'll keep it consistent.
            bucket_threshold = 50
            bucketed_x = round(crack_data["x"] / bucket_threshold) * bucket_threshold
            bucketed_y = round(crack_data["y"] / bucket_threshold) * bucket_threshold
            crack_identifier = f"crack_{bucketed_x}_{bucketed_y}"
            
            previous_crack = db.query(CrackDetection).filter(
                CrackDetection.bridge_id == bridge_id,
                CrackDetection.crack_identifier == crack_identifier
            ).order_by(CrackDetection.detected_at.desc()).first()
            
            crack = CrackDetection(
                bridge_id=bridge_id,
                x=crack_data["x"],
                y=crack_data["y"],
                width=crack_data["width"],
                height=crack_data["height"],
                area=area,
                confidence=crack_data["confidence"],
                severity_level=crack_data["severity"],
                crack_type=crack_data["crack_type"],
                crack_identifier=crack_identifier,
                previous_crack_id=previous_crack.id if previous_crack else None
            )
            db.add(crack)
            db.flush()

            # Attempt deeper linking
            link_to_previous_crack(db, bridge_id, crack)
            
            if previous_crack:
                growth = calculate_crack_growth(crack, previous_crack)
                if growth and growth["grew_significantly"]:
                    significant_growth_count += 1
            
            saved_cracks.append(crack)
        
        high_severity_count = len([c for c in cracks if c["severity"] >= 3])
        
        report = InspectionReport(
            bridge_id=bridge_id,
            report_date=datetime.now(),
            total_cracks_detected=len(cracks),
            high_severity_cracks=high_severity_count
        )
        db.add(report)
        db.commit()
        
        send_urgent_notifications(bridge.bridge_name, high_severity_count)
        if significant_growth_count > 0:
            msg = f"{significant_growth_count} cracks showing significant growth!"
            send_email_notification(bridge.bridge_name, msg)
            send_sms_notification(bridge.bridge_name, msg)
        
        return {
            "message": "Detections saved successfully", 
            "report_id": report.id,
            "significant_growth_count": significant_growth_count
        }
    except Exception as e:
        db.rollback()
        print(f"Error saving detections: {str(e)}")
        return {"error": str(e)}

@router.get("/bridge/{bridge_id}/crack-growth")
async def get_crack_growth_history(bridge_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        return {"error": "Bridge not found"}
    
    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge_id
    ).order_by(CrackDetection.crack_identifier, CrackDetection.detected_at.asc()).all()
    
    crack_history = {}
    for crack in cracks:
        if crack.crack_identifier not in crack_history:
            crack_history[crack.crack_identifier] = []
        
        growth = None
        if crack.previous_crack_id:
            previous_crack = db.query(CrackDetection).filter(CrackDetection.id == crack.previous_crack_id).first()
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
            "growth": growth
        })
    
    return {
        "bridge_name": bridge.bridge_name,
        "crack_history": crack_history
    }

@router.get("/crack/{crack_id}/history")
async def get_crack_history(crack_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    timeline = []
    current = db.query(CrackDetection).filter(CrackDetection.id == crack_id).first()
    if not current:
        raise HTTPException(status_code=404, detail="Crack not found")

    visited = set()
    while current and current.id not in visited:
        visited.add(current.id)
        timeline.append(current)
        if current.previous_crack_id:
            current = db.query(CrackDetection).filter(CrackDetection.id == current.previous_crack_id).first()
        else:
            break

    timeline.reverse()
    growth_pct = None
    growth_per_day = None
    if len(timeline) >= 2:
        first, last = timeline[0], timeline[-1]
        if first.area and first.area > 0:
            growth_pct = round((last.area - first.area) / first.area * 100, 1)
        days = (last.detected_at - first.detected_at).total_seconds() / 86400
        if days > 0 and first.area is not None:
            growth_per_day = round((last.area - first.area) / days, 2)

    return {
        "crack_identifier": timeline[0].crack_identifier if timeline else None,
        "inspection_count": len(timeline),
        "growth_pct": growth_pct,
        "growth_per_day": growth_per_day,
        "history": [
            {
                "id": c.id,
                "detected_at": c.detected_at.isoformat(),
                "area": c.area,
                "width": c.width,
                "height": c.height,
                "confidence": c.confidence,
                "severity_level": c.severity_level,
            }
            for c in timeline
        ],
    }

@router.get("/crack/{crack_id}/prediction")
async def get_crack_prediction(crack_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    history_resp = await get_crack_history(crack_id, db, current_user)
    history = history_resp["history"]
    growth_per_day = history_resp["growth_per_day"] or 0
    
    prediction = predict_crack_maintenance(history, growth_per_day)
    return prediction
