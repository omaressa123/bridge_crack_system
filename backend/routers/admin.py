from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, Bridge, Crack, ImageReview, DatasetImage, ModelVersion, Sensor, AuditLog
from schemas import (
    UserCreate, UserUpdate, UserOut,
    BridgeCreate, BridgeUpdate, BridgeOut,
    CrackUpdate, CrackOut,
    ImageReviewCreate, ImageReviewUpdate, ImageReviewOut,
    DatasetImageCreate, DatasetImageUpdate, DatasetImageOut,
    ModelVersionCreate, ModelVersionUpdate, ModelVersionOut,
    SensorOut,
    AuditLogOut
)
from auth import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])

# User Management
@router.get("/users", response_model=List[UserOut])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(User).all()

@router.post("/users", response_model=UserOut)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(user.password)
    
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        google_id=user.google_id,
        last_login=user.last_login
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# Bridge Management
@router.get("/bridges", response_model=List[BridgeOut])
def get_bridges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(Bridge).all()

@router.post("/bridges", response_model=BridgeOut)
def create_bridge(
    bridge: BridgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_bridge = Bridge(**bridge.dict())
    db.add(db_bridge)
    db.commit()
    db.refresh(db_bridge)
    return db_bridge

@router.get("/bridges/{bridge_id}", response_model=BridgeOut)
def get_bridge(
    bridge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return bridge

@router.put("/bridges/{bridge_id}", response_model=BridgeOut)
def update_bridge(
    bridge_id: int,
    bridge_update: BridgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not db_bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    
    for key, value in bridge_update.dict(exclude_unset=True).items():
        setattr(db_bridge, key, value)
    
    db.commit()
    db.refresh(db_bridge)
    return db_bridge

@router.delete("/bridges/{bridge_id}")
def delete_bridge(
    bridge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found")
    
    db.delete(bridge)
    db.commit()
    return {"message": "Bridge deleted successfully"}

# Crack Management
@router.get("/cracks", response_model=List[CrackOut])
def get_cracks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(Crack).all()

@router.get("/cracks/{crack_id}", response_model=CrackOut)
def get_crack(
    crack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    crack = db.query(Crack).filter(Crack.id == crack_id).first()
    if not crack:
        raise HTTPException(status_code=404, detail="Crack not found")
    return crack

@router.put("/cracks/{crack_id}", response_model=CrackOut)
def update_crack(
    crack_id: int,
    crack_update: CrackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_crack = db.query(Crack).filter(Crack.id == crack_id).first()
    if not db_crack:
        raise HTTPException(status_code=404, detail="Crack not found")
    
    for key, value in crack_update.dict(exclude_unset=True).items():
        setattr(db_crack, key, value)
    
    db.commit()
    db.refresh(db_crack)
    return db_crack

# Image Review System
@router.get("/image-reviews", response_model=List[ImageReviewOut])
def get_image_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(ImageReview).all()

@router.post("/image-reviews", response_model=ImageReviewOut)
def create_image_review(
    review: ImageReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_review = ImageReview(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/image-reviews/{review_id}", response_model=ImageReviewOut)
def get_image_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    review = db.query(ImageReview).filter(ImageReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Image review not found")
    return review

@router.put("/image-reviews/{review_id}", response_model=ImageReviewOut)
def update_image_review(
    review_id: int,
    review_update: ImageReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_review = db.query(ImageReview).filter(ImageReview.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Image review not found")
    
    for key, value in review_update.dict(exclude_unset=True).items():
        setattr(db_review, key, value)
    
    db.commit()
    db.refresh(db_review)
    return db_review

# Dataset Management
@router.get("/dataset-images", response_model=List[DatasetImageOut])
def get_dataset_images(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(DatasetImage).all()

@router.post("/dataset-images", response_model=DatasetImageOut)
def create_dataset_image(
    image: DatasetImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_image = DatasetImage(**image.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@router.get("/dataset-images/{image_id}", response_model=DatasetImageOut)
def get_dataset_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    image = db.query(DatasetImage).filter(DatasetImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Dataset image not found")
    return image

@router.put("/dataset-images/{image_id}", response_model=DatasetImageOut)
def update_dataset_image(
    image_id: int,
    image_update: DatasetImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_image = db.query(DatasetImage).filter(DatasetImage.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Dataset image not found")
    
    for key, value in image_update.dict(exclude_unset=True).items():
        setattr(db_image, key, value)
    
    db.commit()
    db.refresh(db_image)
    return db_image

# Model Management
@router.get("/model-versions", response_model=List[ModelVersionOut])
def get_model_versions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(ModelVersion).all()

@router.post("/model-versions", response_model=ModelVersionOut)
def create_model_version(
    model: ModelVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_model = ModelVersion(**model.dict())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.get("/model-versions/{model_id}", response_model=ModelVersionOut)
def get_model_version(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model version not found")
    return model

@router.put("/model-versions/{model_id}", response_model=ModelVersionOut)
def update_model_version(
    model_id: int,
    model_update: ModelVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    for key, value in model_update.dict(exclude_unset=True).items():
        setattr(db_model, key, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model

# Sensor Management
@router.get("/sensors", response_model=List[SensorOut])
def get_sensors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(Sensor).all()

# Reports
@router.get("/reports/inspection")
def generate_inspection_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # This would generate PDF/Excel reports
    return {"message": "Inspection report generation endpoint"}

@router.get("/reports/maintenance")
def generate_maintenance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # This would generate PDF/Excel reports
    return {"message": "Maintenance report generation endpoint"}

# Audit Log
@router.get("/audit-log", response_model=List[AuditLogOut])
def get_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

# Retraining Queue
@router.get("/retraining-queue/stats")
def get_retraining_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    from sqlalchemy import func
    
    approved_count = db.query(func.count()).filter(DatasetImage.review_status == "approved").scalar()
    rejected_count = db.query(func.count()).filter(DatasetImage.review_status == "rejected").scalar()
    pending_count = db.query(func.count()).filter(DatasetImage.review_status == "pending").scalar()
    training_count = db.query(func.count()).filter(DatasetImage.training_status == "training").scalar()
    validation_count = db.query(func.count()).filter(DatasetImage.training_status == "validation").scalar()
    test_count = db.query(func.count()).filter(DatasetImage.training_status == "test").scalar()
    
    return {
        "approved_images": approved_count,
        "rejected_images": rejected_count,
        "pending_images": pending_count,
        "training_images": training_count,
        "validation_images": validation_count,
        "test_images": test_count
    }

@router.post("/retraining-queue/retrain")
def trigger_retraining(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # This would trigger the retraining process
    return {"message": "Retraining triggered successfully"}

# Notifications
@router.post("/notifications/email")
def send_email_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # This would send email notifications
    return {"message": "Email notification sent"}

@router.post("/notifications/sms")
def send_sms_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # This would send SMS notifications
    return {"message": "SMS notification sent"}
