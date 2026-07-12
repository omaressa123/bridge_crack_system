from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AdminUserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    roles: List[str] = []


class AdminUserCreate(AdminUserBase):
    password: str


class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    roles: Optional[List[str]] = None


class AdminUserOut(AdminUserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    google_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class BridgeBase(BaseModel):
    name: str
    location: str
    gps_coordinates: str
    inspection_schedule: str
    metadata: Dict[str, Any] = {}


class BridgeCreate(BridgeBase):
    pass


class BridgeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    gps_coordinates: Optional[str] = None
    inspection_schedule: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BridgeOut(BridgeBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CrackBase(BaseModel):
    bridge_id: int
    image_url: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]] = []
    severity: str
    label: str
    width: float
    height: float
    area: float
    notes: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected, merged


class CrackCreate(CrackBase):
    pass


class CrackUpdate(BaseModel):
    confidence: Optional[float] = None
    bounding_boxes: Optional[List[Dict[str, Any]]] = None
    severity: Optional[str] = None
    label: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    area: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class CrackOut(CrackBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ImageReviewBase(BaseModel):
    image_url: str
    yolo_prediction: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]] = []
    approved_label: str
    review_status: str = "pending"
    reviewer_id: int
    review_time: datetime
    training_status: str = "not_in_dataset"
    bridge_id: int
    gps: str
    camera: str


class ImageReviewCreate(ImageReviewBase):
    pass


class ImageReviewUpdate(BaseModel):
    yolo_prediction: Optional[str] = None
    confidence: Optional[float] = None
    bounding_boxes: Optional[List[Dict[str, Any]]] = None
    approved_label: Optional[str] = None
    review_status: Optional[str] = None
    training_status: Optional[str] = None


class ImageReviewOut(ImageReviewBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatasetStats(BaseModel):
    approved_images: int
    rejected_images: int
    pending_images: int
    training_images: int
    validation_images: int
    test_images: int


class ModelVersion(BaseModel):
    version: str
    date: datetime
    epochs: int
    mAP50: float
    mAP50_95: float
    precision: float
    recall: float
    training_images: int
    validation_images: int
    weights_url: str
    notes: str
    current_status: str = "draft"  # draft, testing, production


class SensorStatus(BaseModel):
    device_id: str
    status: str
    last_seen: datetime
    battery_level: Optional[float] = None
    signal_strength: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None


class AuditLogEntry(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: datetime
    ip_address: str
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    
    class Config:
        from_attributes = True