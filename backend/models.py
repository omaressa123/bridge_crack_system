from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Bridge(Base):
    __tablename__ = "bridges"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bridge_name = Column(String(255), index=True)
    city = Column(String(100))
    inspection_date = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)   # GIS: bridge location
    longitude = Column(Float, nullable=True)  # GIS: bridge location
    cracks = relationship("CrackDetection", back_populates="bridge", cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="bridge", cascade="all, delete-orphan")
    reports = relationship("InspectionReport", back_populates="bridge", cascade="all, delete-orphan")

class CrackDetection(Base):
    __tablename__ = "crack_detections"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bridge_id = Column(Integer, ForeignKey("bridges.id"))
    x = Column(Float)
    y = Column(Float)
    width = Column(Float)
    height = Column(Float)
    area = Column(Float)  # Calculated area (width * height)
    confidence = Column(Float)
    severity_level = Column(Integer)
    crack_type = Column(String(100))
    crack_identifier = Column(String(255))  # Unique ID to track same crack over time
    previous_crack_id = Column(Integer, ForeignKey("crack_detections.id"), nullable=True)  # Link to previous detection of same crack
    detected_at = Column(DateTime, default=datetime.utcnow)
    bridge = relationship("Bridge", back_populates="cracks")
    previous_crack = relationship("CrackDetection", remote_side=[id])  # Self-referential for previous detection
    report_id = Column(Integer, ForeignKey("inspection_reports.id"), nullable=True)
    report = relationship("InspectionReport", back_populates="cracks")

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bridge_id = Column(Integer, ForeignKey("bridges.id"))
    temperature_c = Column(Float)
    moisture_percent = Column(Float)
    acceleration_x = Column(Float)
    strain_gauge_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    bridge = relationship("Bridge", back_populates="sensor_data")

class InspectionReport(Base):
    __tablename__ = "inspection_reports"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bridge_id = Column(Integer, ForeignKey("bridges.id"))
    report_date = Column(DateTime, default=datetime.utcnow)
    total_cracks_detected = Column(Integer)
    high_severity_cracks = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String(500), nullable=True)
    model_version = Column(String(100), nullable=True)
    status = Column(String(30), default="Pending")
    cracks = relationship(
        "CrackDetection",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    bridge = relationship("Bridge", back_populates="reports")
    creator = relationship("User", back_populates="reports")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    google_id = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    profile_picture = Column(String(500), nullable=True)
    role = Column(String(50), nullable=True, default="Bridge Engineer")
    is_active = Column(Integer, nullable=True, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    reports = relationship("InspectionReport", back_populates="creator")
