import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_admin_user
from models import (
    AdminNotification,
    AuditLog,
    Bridge,
    CrackDetection,
    ModelRegistry,
    ReviewedImage,
    SensorDevice,
    TrainingJob,
    User,
)
from schemas.admin import (
    AdminBridgeCreate,
    AdminBridgeOut,
    AdminBridgeUpdate,
    AdminCrackOut,
    AdminCrackUpdate,
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    AuditLogOut,
    CrackMergeRequest,
    DatasetStatsOut,
    ModelRegistryOut,
    ModelRegistryUpdate,
    NotificationOut,
    RetrainThresholdUpdate,
    ReviewDecision,
    ReviewedImageCreate,
    ReviewedImageOut,
    ReviewedImageUpdate,
    SendNotificationRequest,
    SensorDeviceOut,
    TrainingJobOut,
    parse_json_field,
    serialize_boxes,
)
from services.audit import log_admin_action
from services.notification import send_email_notification, send_sms_notification
from services.prediction import detect_cracks_with_yolo
from services.training import (
    get_dataset_stats,
    get_retrain_threshold,
    run_training_job,
    set_setting,
    start_training_job,
)
from utils.uploads import read_validated_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
BRIDGE_IMG_DIR = UPLOAD_DIR / "bridges"
REVIEW_IMG_DIR = UPLOAD_DIR / "reviews"


def _ensure_upload_dirs():
    BRIDGE_IMG_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_IMG_DIR.mkdir(parents=True, exist_ok=True)


def _bridge_out(bridge: Bridge) -> dict:
    return {
        "id": bridge.id,
        "bridge_name": bridge.bridge_name,
        "city": bridge.city,
        "inspection_date": bridge.inspection_date,
        "latitude": bridge.latitude,
        "longitude": bridge.longitude,
        "image_path": bridge.image_path,
        "inspection_schedule": bridge.inspection_schedule,
        "metadata": bridge.metadata_dict,
        "created_at": bridge.created_at,
        "updated_at": bridge.updated_at,
    }


def _crack_out(crack: CrackDetection, bridge_name: Optional[str] = None) -> dict:
    return {
        "id": crack.id,
        "bridge_id": crack.bridge_id,
        "x": crack.x,
        "y": crack.y,
        "width": crack.width,
        "height": crack.height,
        "area": crack.area,
        "confidence": crack.confidence,
        "severity_level": crack.severity_level,
        "crack_type": crack.crack_type,
        "crack_identifier": crack.crack_identifier,
        "status": crack.status,
        "notes": crack.notes,
        "reviewed_by": crack.reviewed_by,
        "reviewed_at": crack.reviewed_at,
        "detected_at": crack.detected_at,
        "bridge_name": bridge_name,
    }


def _review_out(img: ReviewedImage) -> dict:
    return {
        "id": img.id,
        "bridge_id": img.bridge_id,
        "original_image_path": img.original_image_path,
        "annotated_image_path": img.annotated_image_path,
        "prediction": parse_json_field(img.prediction_json),
        "approved_label": img.approved_label,
        "review_status": img.review_status,
        "reviewer_id": img.reviewer_id,
        "review_time": img.review_time,
        "training_status": img.training_status,
        "camera": img.camera,
        "confidence": img.confidence,
        "bounding_boxes": parse_json_field(img.bounding_boxes_json, []),
        "latitude": img.latitude,
        "longitude": img.longitude,
        "severity": img.severity,
        "width": img.width,
        "height": img.height,
        "area": img.area,
        "notes": img.notes,
        "created_at": img.created_at,
    }


def _model_out(model: ModelRegistry) -> dict:
    return {
        "id": model.id,
        "version": model.version,
        "trained_at": model.trained_at,
        "epochs": model.epochs,
        "map50": model.map50,
        "map50_95": model.map50_95,
        "precision_score": model.precision_score,
        "recall_score": model.recall_score,
        "training_images": model.training_images,
        "validation_images": model.validation_images,
        "weights_path": model.weights_path,
        "confusion_matrix_path": model.confusion_matrix_path,
        "metrics": parse_json_field(model.metrics_json),
        "notes": model.notes,
        "status": model.status,
        "created_at": model.created_at,
    }


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get("/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return {
        "users": db.query(User).count(),
        "bridges": db.query(Bridge).count(),
        "cracks": db.query(CrackDetection).count(),
        "pending_reviews": db.query(ReviewedImage).filter(ReviewedImage.review_status == "pending").count(),
        "dataset": get_dataset_stats(db),
        "models": db.query(ModelRegistry).count(),
        "production_model": db.query(ModelRegistry).filter(ModelRegistry.status == "production").count(),
        "unread_notifications": db.query(AdminNotification).filter(AdminNotification.is_read == False).count(),
    }


# ── User Management ───────────────────────────────────────────────────────────

@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    google_id = payload.google_id or f"admin-created-{uuid.uuid4().hex[:12]}"
    user = User(
        google_id=google_id,
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_admin_action(db, user_id=admin.id, action="user.create", request=request, entity_type="user", entity_id=user.id, after=user.email)
    return user


@router.get("/users/{user_id}", response_model=AdminUserOut)
def get_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    before = {"email": user.email, "role": user.role, "is_active": user.is_active}
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    log_admin_action(db, user_id=admin.id, action="user.update", request=request, entity_type="user", entity_id=user.id, before=before, after=payload.model_dump(exclude_unset=True))
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    email = user.email
    db.delete(user)
    db.commit()
    log_admin_action(db, user_id=admin.id, action="user.delete", request=request, entity_type="user", entity_id=user_id, before=email)
    return {"message": "User deleted"}


@router.post("/users/{user_id}/toggle-active", response_model=AdminUserOut)
def toggle_user_active(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    before = user.is_active
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    log_admin_action(db, user_id=admin.id, action="user.toggle_active", request=request, entity_type="user", entity_id=user_id, before=before, after=user.is_active)
    return user


# ── Bridge Management ─────────────────────────────────────────────────────────

@router.get("/bridges", response_model=List[AdminBridgeOut])
def list_bridges(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    bridges = db.query(Bridge).order_by(Bridge.bridge_name).all()
    return [_bridge_out(b) for b in bridges]


@router.post("/bridges", response_model=AdminBridgeOut, status_code=status.HTTP_201_CREATED)
def create_bridge(
    payload: AdminBridgeCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    bridge = Bridge(
        bridge_name=payload.bridge_name,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
        inspection_schedule=payload.inspection_schedule,
        metadata_json=json.dumps(payload.metadata) if payload.metadata else None,
        inspection_date=datetime.utcnow(),
    )
    db.add(bridge)
    db.commit()
    db.refresh(bridge)
    log_admin_action(db, user_id=admin.id, action="bridge.create", request=request, entity_type="bridge", entity_id=bridge.id, after=bridge.bridge_name)
    return _bridge_out(bridge)


@router.put("/bridges/{bridge_id}", response_model=AdminBridgeOut)
def update_bridge(
    bridge_id: int,
    payload: AdminBridgeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    data = payload.model_dump(exclude_unset=True)
    if "metadata" in data:
        bridge.metadata_json = json.dumps(data.pop("metadata"))
    for key, value in data.items():
        setattr(bridge, key, value)
    db.commit()
    db.refresh(bridge)
    log_admin_action(db, user_id=admin.id, action="bridge.update", request=request, entity_type="bridge", entity_id=bridge_id, after=data)
    return _bridge_out(bridge)


@router.delete("/bridges/{bridge_id}")
def delete_bridge(
    bridge_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    name = bridge.bridge_name
    db.delete(bridge)
    db.commit()
    log_admin_action(db, user_id=admin.id, action="bridge.delete", request=request, entity_type="bridge", entity_id=bridge_id, before=name)
    return {"message": "Bridge deleted"}


@router.post("/bridges/{bridge_id}/image")
async def upload_bridge_image(
    bridge_id: int,
    image: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    _ensure_upload_dirs()
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    contents = await read_validated_image(image)
    ext = Path(image.filename or "bridge.jpg").suffix or ".jpg"
    filename = f"bridge_{bridge_id}_{uuid.uuid4().hex[:8]}{ext}"
    path = BRIDGE_IMG_DIR / filename
    path.write_bytes(contents)
    bridge.image_path = str(path)
    db.commit()
    log_admin_action(db, user_id=admin.id, action="bridge.upload_image", request=request, entity_type="bridge", entity_id=bridge_id, after=str(path))
    return {"image_path": str(path)}


# ── Crack Management ──────────────────────────────────────────────────────────

@router.get("/cracks", response_model=List[AdminCrackOut])
def list_cracks(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    bridge_id: Optional[int] = Query(None),
    severity_min: Optional[int] = Query(None, ge=1, le=3),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(CrackDetection, Bridge.bridge_name).join(Bridge, CrackDetection.bridge_id == Bridge.id)
    if status_filter:
        query = query.filter(CrackDetection.status == status_filter)
    if bridge_id:
        query = query.filter(CrackDetection.bridge_id == bridge_id)
    if severity_min:
        query = query.filter(CrackDetection.severity_level >= severity_min)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                CrackDetection.crack_type.ilike(like),
                CrackDetection.crack_identifier.ilike(like),
                CrackDetection.notes.ilike(like),
            )
        )
    rows = query.order_by(CrackDetection.detected_at.desc()).limit(500).all()
    return [_crack_out(c, name) for c, name in rows]


@router.put("/cracks/{crack_id}", response_model=AdminCrackOut)
def update_crack(
    crack_id: int,
    payload: AdminCrackUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    crack = db.query(CrackDetection).filter(CrackDetection.id == crack_id).first()
    if not crack:
        raise HTTPException(status_code=404, detail="Crack not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(crack, key, value)
    if payload.width is not None or payload.height is not None:
        crack.area = crack.width * crack.height
    db.commit()
    db.refresh(crack)
    bridge = db.query(Bridge).filter(Bridge.id == crack.bridge_id).first()
    log_admin_action(db, user_id=admin.id, action="crack.update", request=request, entity_type="crack", entity_id=crack_id)
    return _crack_out(crack, bridge.bridge_name if bridge else None)


@router.post("/cracks/{crack_id}/approve", response_model=AdminCrackOut)
def approve_crack(crack_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    crack = db.query(CrackDetection).filter(CrackDetection.id == crack_id).first()
    if not crack:
        raise HTTPException(status_code=404, detail="Crack not found")
    crack.status = "approved"
    crack.reviewed_by = admin.id
    crack.reviewed_at = datetime.utcnow()
    db.commit()
    bridge = db.query(Bridge).filter(Bridge.id == crack.bridge_id).first()
    log_admin_action(db, user_id=admin.id, action="crack.approve", request=request, entity_type="crack", entity_id=crack_id)
    return _crack_out(crack, bridge.bridge_name if bridge else None)


@router.post("/cracks/{crack_id}/reject", response_model=AdminCrackOut)
def reject_crack(crack_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    crack = db.query(CrackDetection).filter(CrackDetection.id == crack_id).first()
    if not crack:
        raise HTTPException(status_code=404, detail="Crack not found")
    crack.status = "rejected"
    crack.reviewed_by = admin.id
    crack.reviewed_at = datetime.utcnow()
    db.commit()
    bridge = db.query(Bridge).filter(Bridge.id == crack.bridge_id).first()
    log_admin_action(db, user_id=admin.id, action="crack.reject", request=request, entity_type="crack", entity_id=crack_id)
    return _crack_out(crack, bridge.bridge_name if bridge else None)


@router.post("/cracks/merge", response_model=AdminCrackOut)
def merge_cracks(
    payload: CrackMergeRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    cracks = db.query(CrackDetection).filter(CrackDetection.id.in_(payload.crack_ids)).all()
    if len(cracks) < 2:
        raise HTTPException(status_code=400, detail="At least two cracks required")

    target_id = payload.target_crack_id or cracks[0].id
    target = next((c for c in cracks if c.id == target_id), cracks[0])
    identifier = target.crack_identifier or f"merged_{target.id}"

    for crack in cracks:
        if crack.id == target.id:
            crack.status = "approved"
            crack.crack_identifier = identifier
            continue
        crack.status = "merged"
        crack.crack_identifier = identifier
        crack.previous_crack_id = target.id
        crack.reviewed_by = admin.id
        crack.reviewed_at = datetime.utcnow()

    db.commit()
    bridge = db.query(Bridge).filter(Bridge.id == target.bridge_id).first()
    log_admin_action(db, user_id=admin.id, action="crack.merge", request=request, entity_type="crack", entity_id=target.id, after=payload.crack_ids)
    return _crack_out(target, bridge.bridge_name if bridge else None)


@router.delete("/cracks/{crack_id}")
def delete_crack(crack_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    crack = db.query(CrackDetection).filter(CrackDetection.id == crack_id).first()
    if not crack:
        raise HTTPException(status_code=404, detail="Crack not found")
    db.delete(crack)
    db.commit()
    log_admin_action(db, user_id=admin.id, action="crack.delete", request=request, entity_type="crack", entity_id=crack_id)
    return {"message": "Crack deleted"}


# ── Image Review ──────────────────────────────────────────────────────────────

@router.get("/image-reviews", response_model=List[ReviewedImageOut])
def list_image_reviews(
    review_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(ReviewedImage)
    if review_status:
        query = query.filter(ReviewedImage.review_status == review_status)
    images = query.order_by(ReviewedImage.created_at.desc()).limit(200).all()
    return [_review_out(img) for img in images]


@router.post("/image-reviews/upload", response_model=ReviewedImageOut, status_code=status.HTTP_201_CREATED)
async def upload_for_review(
    image: UploadFile = File(...),
    bridge_id: Optional[int] = Query(None),
    camera: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    _ensure_upload_dirs()
    contents = await read_validated_image(image)
    ext = Path(image.filename or "review.jpg").suffix or ".jpg"
    filename = f"review_{uuid.uuid4().hex[:12]}{ext}"
    path = REVIEW_IMG_DIR / filename
    path.write_bytes(contents)

    predictions = []
    confidence = None
    boxes = []
    try:
        predictions = detect_cracks_with_yolo(contents)
        if predictions:
            confidence = max(p["confidence"] for p in predictions)
            boxes = [
                {
                    "x": p["x"], "y": p["y"],
                    "width": p["width"], "height": p["height"],
                    "class_id": 0, "label": p.get("crack_type", "crack"),
                    "confidence": p["confidence"],
                }
                for p in predictions
            ]
    except Exception as exc:
        logger.warning("YOLO prediction failed on upload: %s", exc)

    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first() if bridge_id else None
    reviewed = ReviewedImage(
        bridge_id=bridge_id,
        original_image_path=str(path),
        prediction_json=json.dumps(predictions),
        confidence=confidence,
        bounding_boxes_json=json.dumps(boxes),
        review_status="pending",
        training_status="pending",
        camera=camera,
        latitude=bridge.latitude if bridge else None,
        longitude=bridge.longitude if bridge else None,
    )
    db.add(reviewed)
    db.commit()
    db.refresh(reviewed)
    return _review_out(reviewed)


@router.post("/image-reviews/{review_id}/decide", response_model=ReviewedImageOut)
def decide_image_review(
    review_id: int,
    payload: ReviewDecision,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    img = db.query(ReviewedImage).filter(ReviewedImage.id == review_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image review not found")

    img.approved_label = "crack" if payload.decision == "crack" else "no_crack"
    img.review_status = "approved" if payload.decision == "crack" else "rejected"
    img.reviewer_id = admin.id
    img.review_time = datetime.utcnow()

    if payload.bounding_boxes is not None:
        img.bounding_boxes_json = serialize_boxes(payload.bounding_boxes)
    if payload.severity is not None:
        img.severity = payload.severity
    if payload.width is not None:
        img.width = payload.width
    if payload.height is not None:
        img.height = payload.height
    if payload.area is not None:
        img.area = payload.area
    if payload.notes is not None:
        img.notes = payload.notes

    if img.review_status == "approved":
        img.training_status = "queued"
        stats = get_dataset_stats(db)
        threshold = get_retrain_threshold(db)
        if stats["approved_images"] + 1 >= threshold:
            db.add(AdminNotification(
                title="New training data available",
                message=f"{stats['approved_images'] + 1} approved images reached threshold of {threshold}.",
                notification_type="training",
            ))

    db.commit()
    db.refresh(img)
    log_admin_action(db, user_id=admin.id, action="image_review.decide", request=request, entity_type="reviewed_image", entity_id=review_id, after=payload.decision)
    return _review_out(img)


@router.put("/image-reviews/{review_id}", response_model=ReviewedImageOut)
def update_image_review(
    review_id: int,
    payload: ReviewedImageUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    img = db.query(ReviewedImage).filter(ReviewedImage.id == review_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image review not found")
    data = payload.model_dump(exclude_unset=True)
    if "bounding_boxes" in data:
        img.bounding_boxes_json = serialize_boxes(data.pop("bounding_boxes"))
    for key, value in data.items():
        setattr(img, key, value)
    db.commit()
    db.refresh(img)
    log_admin_action(db, user_id=admin.id, action="image_review.update", request=request, entity_type="reviewed_image", entity_id=review_id)
    return _review_out(img)


@router.get("/image-reviews/{review_id}/image")
def serve_review_image(review_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    img = db.query(ReviewedImage).filter(ReviewedImage.id == review_id).first()
    if not img or not Path(img.original_image_path).exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img.original_image_path)


# ── Dataset & Retraining ──────────────────────────────────────────────────────

@router.get("/dataset/stats", response_model=DatasetStatsOut)
def dataset_stats(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return get_dataset_stats(db)


@router.get("/dataset/images", response_model=List[ReviewedImageOut])
def dataset_images(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    images = db.query(ReviewedImage).order_by(ReviewedImage.created_at.desc()).all()
    return [_review_out(img) for img in images]


@router.put("/dataset/threshold")
def update_retrain_threshold(
    payload: RetrainThresholdUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    set_setting(db, "retrain_threshold", str(payload.threshold))
    log_admin_action(db, user_id=admin.id, action="dataset.update_threshold", request=request, after=payload.threshold)
    return {"threshold": payload.threshold}


@router.post("/retraining/start", response_model=TrainingJobOut)
def start_retraining(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    stats = get_dataset_stats(db)
    if not stats["ready_for_retrain"]:
        raise HTTPException(status_code=400, detail="Not enough approved images for retraining")
    job = start_training_job(db)
    background_tasks.add_task(run_training_job, job.id)
    log_admin_action(db, user_id=admin.id, action="retraining.start", request=request, entity_id=job.id)
    return job


@router.get("/retraining/jobs", response_model=List[TrainingJobOut])
def list_training_jobs(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).limit(20).all()


@router.get("/retraining/jobs/{job_id}", response_model=TrainingJobOut)
def get_training_job(job_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


# ── Model Registry ────────────────────────────────────────────────────────────

@router.get("/models", response_model=List[ModelRegistryOut])
def list_models(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    models = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()
    return [_model_out(m) for m in models]


@router.put("/models/{model_id}", response_model=ModelRegistryOut)
def update_model(
    model_id: int,
    payload: ModelRegistryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    log_admin_action(db, user_id=admin.id, action="model.update", request=request, entity_type="model", entity_id=model_id)
    return _model_out(model)


@router.post("/models/{model_id}/deploy", response_model=ModelRegistryOut)
def deploy_model(
    model_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.query(ModelRegistry).filter(ModelRegistry.status == "production").update({"status": "archived"})
    model.status = "production"
    db.commit()
    db.refresh(model)
    log_admin_action(db, user_id=admin.id, action="model.deploy", request=request, entity_type="model", entity_id=model_id, after=model.version)
    return _model_out(model)


@router.post("/models/{model_id}/rollback", response_model=ModelRegistryOut)
def rollback_model(
    model_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return deploy_model(model_id, request, db, admin)


# ── Sensors ───────────────────────────────────────────────────────────────────

@router.get("/sensors", response_model=List[SensorDeviceOut])
def list_sensors(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    rows = db.query(SensorDevice, Bridge.bridge_name).outerjoin(Bridge).all()
    return [
        {
            "id": s.id,
            "bridge_id": s.bridge_id,
            "device_id": s.device_id,
            "mqtt_topic": s.mqtt_topic,
            "status": s.status,
            "last_seen": s.last_seen,
            "battery_level": s.battery_level,
            "signal_strength": s.signal_strength,
            "bridge_name": name,
        }
        for s, name in rows
    ]


@router.post("/sensors/reconnect")
def reconnect_sensors(request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    from services.mqtt import start_mqtt_listener
    from routers import sensors as sensors_router

    start_mqtt_listener(
        active_websockets=sensors_router.connected_websockets,
        broadcast_fn=sensors_router.broadcast_to_dashboards,
    )
    log_admin_action(db, user_id=admin.id, action="sensors.reconnect", request=request)
    return {"message": "MQTT listener restarted"}


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports/inspection/pdf")
def inspection_report_pdf(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    from services.pdf import generate_inspection_pdf
    from models import InspectionReport

    reports = db.query(InspectionReport).order_by(InspectionReport.report_date.desc()).limit(50).all()
    path = generate_inspection_pdf(reports)
    if not path or not Path(path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
    return FileResponse(path, filename="inspection_report.pdf", media_type="application/pdf")


@router.get("/reports/maintenance/excel")
def maintenance_report_excel(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=501, detail="openpyxl not installed")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Maintenance"
    ws.append(["Bridge", "Crack ID", "Severity", "Area", "Status", "Detected At"])
    rows = (
        db.query(CrackDetection, Bridge.bridge_name)
        .join(Bridge)
        .filter(CrackDetection.severity_level >= 2)
        .order_by(CrackDetection.detected_at.desc())
        .limit(500)
        .all()
    )
    for crack, bridge_name in rows:
        ws.append([bridge_name, crack.id, crack.severity_level, crack.area, crack.status, crack.detected_at.isoformat()])

    out = UPLOAD_DIR / "maintenance_report.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return FileResponse(str(out), filename="maintenance_report.xlsx")


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationOut])
def list_notifications(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(AdminNotification).order_by(AdminNotification.created_at.desc()).limit(50).all()


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    n = db.query(AdminNotification).filter(AdminNotification.id == notification_id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "ok"}


@router.post("/notifications/send")
def send_notification(
    payload: SendNotificationRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    db.add(AdminNotification(title=payload.title, message=payload.message, notification_type=payload.notification_type))
    db.commit()
    if payload.send_email and payload.bridge_name:
        send_email_notification(payload.bridge_name, payload.message)
    log_admin_action(db, user_id=admin.id, action="notification.send", request=request, after=payload.title)
    return {"message": "Notification sent"}


@router.post("/notifications/sms")
def send_sms(payload: SendNotificationRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    if payload.bridge_name:
        send_sms_notification(payload.bridge_name, payload.message)
    return {"message": "SMS queued (future-ready)"}


# ── Audit Log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log", response_model=List[AuditLogOut])
def audit_log(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    rows = (
        db.query(AuditLog, User.full_name)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": name,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "ip_address": log.ip_address,
            "before_value": log.before_value,
            "after_value": log.after_value,
            "timestamp": log.timestamp,
        }
        for log, name in rows
    ]
