import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class Bridge(Base):
    __tablename__ = "bridges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bridge_name = Column(String(255), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    inspection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    image_path = Column(String(500), nullable=True)
    inspection_schedule = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def metadata_dict(self) -> dict:
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    cracks = relationship(
        "CrackDetection",
        back_populates="bridge",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sensor_data = relationship(
        "SensorData",
        back_populates="bridge",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports = relationship(
        "InspectionReport",
        back_populates="bridge",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CrackDetection(Base):
    __tablename__ = "crack_detections"
    __table_args__ = (
        Index("ix_crack_bridge_detected", "bridge_id", "detected_at"),
        Index("ix_crack_bridge_identifier", "bridge_id", "crack_identifier"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bridge_id = Column(
        Integer,
        ForeignKey("bridges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    area = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    severity_level = Column(Integer, nullable=False, default=1)
    crack_type = Column(String(100), nullable=False, default="unknown")
    crack_identifier = Column(String(255), nullable=True, index=True)
    previous_crack_id = Column(
        Integer,
        ForeignKey("crack_detections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_id = Column(
        Integer,
        ForeignKey("inspection_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(30), nullable=False, default="pending", index=True)
    notes = Column(Text, nullable=True)
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    bridge = relationship("Bridge", back_populates="cracks")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    previous_crack = relationship(
        "CrackDetection",
        remote_side=[id],
        foreign_keys=[previous_crack_id],
    )
    report = relationship("InspectionReport", back_populates="cracks")


class SensorData(Base):
    __tablename__ = "sensor_data"
    __table_args__ = (
        Index("ix_sensor_bridge_timestamp", "bridge_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bridge_id = Column(
        Integer,
        ForeignKey("bridges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    temperature_c = Column(Float, nullable=True)
    moisture_percent = Column(Float, nullable=True)
    acceleration_x = Column(Float, nullable=True)
    strain_gauge_value = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    bridge = relationship("Bridge", back_populates="sensor_data")


class InspectionReport(Base):
    __tablename__ = "inspection_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bridge_id = Column(
        Integer,
        ForeignKey("bridges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    total_cracks_detected = Column(Integer, nullable=False, default=0)
    high_severity_cracks = Column(Integer, nullable=False, default=0)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    image_path = Column(String(500), nullable=True)
    model_version = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="Pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    cracks = relationship("CrackDetection", back_populates="report")
    bridge = relationship("Bridge", back_populates="reports")
    creator = relationship("User", back_populates="reports")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    profile_picture = Column(String(500), nullable=True)
    role = Column(String(50), nullable=False, default="Bridge Engineer")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("InspectionReport", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")
    reviewed_images = relationship("ReviewedImage", back_populates="reviewer")


class ReviewedImage(Base):
    __tablename__ = "reviewed_images"
    __table_args__ = (
        Index("ix_reviewed_bridge_status", "bridge_id", "review_status"),
        Index("ix_reviewed_training_status", "training_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bridge_id = Column(
        Integer,
        ForeignKey("bridges.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    original_image_path = Column(String(500), nullable=False)
    annotated_image_path = Column(String(500), nullable=True)
    prediction_json = Column(Text, nullable=True)
    approved_label = Column(String(50), nullable=True)
    review_status = Column(String(30), nullable=False, default="pending", index=True)
    reviewer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    review_time = Column(DateTime, nullable=True)
    training_status = Column(String(30), nullable=False, default="pending", index=True)
    camera = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    bounding_boxes_json = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    severity = Column(Integer, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    area = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    bridge = relationship("Bridge")
    reviewer = relationship("User", back_populates="reviewed_images")


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, unique=True, index=True)
    trained_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    epochs = Column(Integer, nullable=False, default=0)
    map50 = Column(Float, nullable=True)
    map50_95 = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    training_images = Column(Integer, nullable=False, default=0)
    validation_images = Column(Integer, nullable=False, default=0)
    weights_path = Column(String(500), nullable=True)
    confusion_matrix_path = Column(String(500), nullable=True)
    metrics_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="draft", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(30), nullable=False, default="queued", index=True)
    progress = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    model_version_id = Column(
        Integer,
        ForeignKey("model_registry.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    model_version = relationship("ModelRegistry")


class SensorDevice(Base):
    __tablename__ = "sensor_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bridge_id = Column(
        Integer,
        ForeignKey("bridges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id = Column(String(100), nullable=False, unique=True, index=True)
    mqtt_topic = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False, default="disconnected", index=True)
    last_seen = Column(DateTime, nullable=True)
    battery_level = Column(Float, nullable=True)
    signal_strength = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    bridge = relationship("Bridge")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_user_timestamp", "user_id", "timestamp"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    before_value = Column(Text, nullable=True)
    after_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminNotification(Base):
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default="info")
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
