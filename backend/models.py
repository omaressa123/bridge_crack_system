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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    bridge = relationship("Bridge", back_populates="cracks")
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
