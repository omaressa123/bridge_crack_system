import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Users ──────────────────────────────────────────────────────────────────

class AdminUserOut(BaseModel):
    id: int
    google_id: str
    full_name: str
    email: str
    profile_picture: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    email: str
    full_name: str
    role: str = "Bridge Engineer"
    google_id: Optional[str] = None
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ── Bridges ─────────────────────────────────────────────────────────────────

class AdminBridgeOut(BaseModel):
    id: int
    bridge_name: str
    city: str
    inspection_date: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_path: Optional[str] = None
    inspection_schedule: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminBridgeCreate(BaseModel):
    bridge_name: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    inspection_schedule: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AdminBridgeUpdate(BaseModel):
    bridge_name: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    inspection_schedule: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    inspection_date: Optional[datetime] = None


# ── Cracks ────────────────────────────────────────────────────────────────────

class AdminCrackOut(BaseModel):
    id: int
    bridge_id: int
    x: float
    y: float
    width: float
    height: float
    area: float
    confidence: float
    severity_level: int
    crack_type: str
    crack_identifier: Optional[str] = None
    status: str
    notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    detected_at: datetime
    bridge_name: Optional[str] = None

    class Config:
        from_attributes = True


class AdminCrackUpdate(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    confidence: Optional[float] = None
    severity_level: Optional[int] = Field(None, ge=1, le=3)
    crack_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CrackMergeRequest(BaseModel):
    crack_ids: List[int] = Field(..., min_length=2)
    target_crack_id: Optional[int] = None


# ── Image Review ──────────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    class_id: int = 0
    label: str = "crack"
    confidence: Optional[float] = None


class ReviewedImageOut(BaseModel):
    id: int
    bridge_id: Optional[int] = None
    original_image_path: str
    annotated_image_path: Optional[str] = None
    prediction: Optional[Dict[str, Any]] = None
    approved_label: Optional[str] = None
    review_status: str
    reviewer_id: Optional[int] = None
    review_time: Optional[datetime] = None
    training_status: str
    camera: Optional[str] = None
    confidence: Optional[float] = None
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: Optional[int] = None
    width: Optional[float] = None
    height: Optional[float] = None
    area: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewedImageCreate(BaseModel):
    bridge_id: Optional[int] = None
    original_image_path: str
    prediction: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    camera: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ReviewedImageUpdate(BaseModel):
    approved_label: Optional[str] = None
    review_status: Optional[str] = None
    bounding_boxes: Optional[List[BoundingBox]] = None
    severity: Optional[int] = Field(None, ge=1, le=3)
    width: Optional[float] = None
    height: Optional[float] = None
    area: Optional[float] = None
    notes: Optional[str] = None
    training_status: Optional[str] = None


class ReviewDecision(BaseModel):
    decision: str = Field(..., pattern="^(crack|no_crack)$")
    bounding_boxes: Optional[List[BoundingBox]] = None
    severity: Optional[int] = Field(None, ge=1, le=3)
    width: Optional[float] = None
    height: Optional[float] = None
    area: Optional[float] = None
    notes: Optional[str] = None


# ── Model Registry ────────────────────────────────────────────────────────────

class ModelRegistryOut(BaseModel):
    id: int
    version: str
    trained_at: datetime
    epochs: int
    map50: Optional[float] = None
    map50_95: Optional[float] = None
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    training_images: int
    validation_images: int
    weights_path: Optional[str] = None
    confusion_matrix_path: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ModelRegistryUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = None


# ── Sensors ───────────────────────────────────────────────────────────────────

class SensorDeviceOut(BaseModel):
    id: int
    bridge_id: int
    device_id: str
    mqtt_topic: Optional[str] = None
    status: str
    last_seen: Optional[datetime] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[int] = None
    bridge_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SendNotificationRequest(BaseModel):
    title: str
    message: str
    notification_type: str = "info"
    send_email: bool = False
    bridge_name: Optional[str] = None


class RetrainThresholdUpdate(BaseModel):
    threshold: int = Field(..., ge=1, le=10000)


class TrainingJobOut(BaseModel):
    id: int
    status: str
    progress: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_version_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetStatsOut(BaseModel):
    approved_images: int
    rejected_images: int
    pending_images: int
    training_images: int
    validation_images: int
    test_images: int
    retrain_threshold: int
    ready_for_retrain: bool


def parse_json_field(raw: Optional[str], default=None):
    if not raw:
        return default if default is not None else {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def serialize_boxes(boxes: Optional[List[BoundingBox]]) -> Optional[str]:
    if boxes is None:
        return None
    return json.dumps([b.model_dump() for b in boxes])
