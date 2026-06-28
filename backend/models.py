from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

Base = declarative_base()

class Bridge(Base):
    __tablename__ = "bridges"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bridge_name = Column(String(255), index=True)
    city = Column(String(100))
    inspection_date = Column(DateTime, default=datetime.utcnow)
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
    confidence = Column(Float)
    severity_level = Column(Integer)
    crack_type = Column(String(100))
    detected_at = Column(DateTime, default=datetime.utcnow)
    bridge = relationship("Bridge", back_populates="cracks")

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
    bridge = relationship("Bridge", back_populates="reports")

# Construct MySQL database URL from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "bridge_crack_db")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
