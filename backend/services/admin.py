from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from backend.database import get_db
from backend.models import User, Bridge, Crack, ImageReview, Dataset, ModelVersion, Sensor, AuditLog
from backend.schemas.admin import AdminUserCreate, AdminUserUpdate, AdminBridgeCreate, AdminBridgeUpdate, AdminCrackUpdate, AdminImageReviewUpdate, AdminDatasetCreate, AdminModelVersionCreate, AdminSensorUpdate
from backend.deps import get_current_admin_user


class AdminService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # User Management
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create_user(self, user_in: AdminUserCreate) -> User:
        user = User(**user_in.dict())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, user_id: int, user_in: AdminUserUpdate) -> User:
        user = self.get_user(user_id)
        for key, value in user_in.dict(exclude_unset=True).items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int):
        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()

    def toggle_user_status(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user.is_active = not user.is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    # Bridge Management
    def get_bridges(self, skip: int = 0, limit: int = 100) -> List[Bridge]:
        return self.db.query(Bridge).offset(skip).limit(limit).all()

    def create_bridge(self, bridge_in: AdminBridgeCreate) -> Bridge:
        bridge = Bridge(**bridge_in.dict())
        self.db.add(bridge)
        self.db.commit()
        self.db.refresh(bridge)
        return bridge

    def get_bridge(self, bridge_id: int) -> Bridge:
        bridge = self.db.query(Bridge).filter(Bridge.id == bridge_id).first()
        if not bridge:
            raise HTTPException(status_code=404, detail="Bridge not found")
        return bridge

    def update_bridge(self, bridge_id: int, bridge_in: AdminBridgeUpdate) -> Bridge:
        bridge = self.get_bridge(bridge_id)
        for key, value in bridge_in.dict(exclude_unset=True).items():
            setattr(bridge, key, value)
        self.db.commit()
        self.db.refresh(bridge)
        return bridge

    def delete_bridge(self, bridge_id: int):
        bridge = self.get_bridge(bridge_id)
        self.db.delete(bridge)
        self.db.commit()

    # Crack Management
    def get_cracks(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Crack]:
        query = self.db.query(Crack)
        if status:
            query = query.filter(Crack.status == status)
        return query.offset(skip).limit(limit).all()

    def update_crack(self, crack_id: int, crack_in: AdminCrackUpdate) -> Crack:
        crack = self.db.query(Crack).filter(Crack.id == crack_id).first()
        if not crack:
            raise HTTPException(status_code=404, detail="Crack not found")
        for key, value in crack_in.dict(exclude_unset=True).items():
            setattr(crack, key, value)
        self.db.commit()
        self.db.refresh(crack)
        return crack

    def approve_crack(self, crack_id: int) -> Crack:
        crack = self.get_crack(crack_id)
        crack.status = "approved"
        self.db.commit()
        self.db.refresh(crack)
        return crack

    def reject_crack(self, crack_id: int) -> Crack:
        crack = self.get_crack(crack_id)
        crack.status = "rejected"
        self.db.commit()
        self.db.refresh(crack)
        return crack

    def merge_cracks(self, crack_ids: List[int]) -> Crack:
        # Implementation for merging cracks
        pass

    def delete_crack(self, crack_id: int):
        crack = self.db.query(Crack).filter(Crack.id == crack_id).first()
        if crack:
            self.db.delete(crack)
            self.db.commit()

    # Image Review System
    def get_image_reviews(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[ImageReview]:
        query = self.db.query(ImageReview)
        if status:
            query = query.filter(ImageReview.review_status == status)
        return query.offset(skip).limit(limit).all()

    def update_image_review(self, review_id: int, review_in: AdminImageReviewUpdate) -> ImageReview:
        review = self.db.query(ImageReview).filter(ImageReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Image review not found")
        for key, value in review_in.dict(exclude_unset=True).items():
            setattr(review, key, value)
        self.db.commit()
        self.db.refresh(review)
        return review

    # Dataset Management
    def create_dataset(self, dataset_in: AdminDatasetCreate) -> Dataset:
        dataset = Dataset(**dataset_in.dict())
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def get_datasets(self, skip: int = 0, limit: int = 100) -> List[Dataset]:
        return self.db.query(Dataset).offset(skip).limit(limit).all()

    # Model Management
    def create_model_version(self, model_in: AdminModelVersionCreate) -> ModelVersion:
        model = ModelVersion(**model_in.dict())
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_model_versions(self, skip: int = 0, limit: int = 100) -> List[ModelVersion]:
        return self.db.query(ModelVersion).offset(skip).limit(limit).all()

    def set_production_model(self, model_id: int):
        # Set current model as production
        self.db.query(ModelVersion).update({ModelVersion.is_production: False})
        model = self.db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if model:
            model.is_production = True
            self.db.commit()
            self.db.refresh(model)
        return model

    # Sensor Management
    def get_sensors(self, skip: int = 0, limit: int = 100) -> List[Sensor]:
        return self.db.query(Sensor).offset(skip).limit(limit).all()

    def update_sensor(self, sensor_id: int, sensor_in: AdminSensorUpdate) -> Sensor:
        sensor = self.db.query(Sensor).filter(Sensor.id == sensor_id).first()
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
        for key, value in sensor_in.dict(exclude_unset=True).items():
            setattr(sensor, key, value)
        self.db.commit()
        self.db.refresh(sensor)
        return sensor

    # Audit Log
    def log_audit(self, user_id: int, action: str, details: str, before_value: str = None, after_value: str = None):
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            before_value=before_value,
            after_value=after_value
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

# Dependency injection
def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)