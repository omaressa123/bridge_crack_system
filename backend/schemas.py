from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class GoogleLoginRequest(BaseModel):
    credential: str

class CrackBase(BaseModel):
    x: float
    y: float
    width: float
    height: float
    confidence: float
    severity: int
    crack_type: str

class CrackSaveRequest(BaseModel):
    cracks: List[CrackBase]

class SensorDataResponse(BaseModel):
    temperature_history: List[float]
    moisture_history: List[float]
    vibration_history: List[float]
    strain_history: List[float]
    timestamps: List[str]

class BridgeBase(BaseModel):
    id: int
    name: str
    city: str

class BridgeListResponse(BaseModel):
    bridges: List[BridgeBase]

class BridgeStatusResponse(BaseModel):
    bridge_name: str
    city: str
    overall_severity: int
    total_cracks: int
    high_severity_cracks: int
    last_inspection_date: str
    recommendation: str
    current_sensors: Dict[str, float]

class InspectionReportBrief(BaseModel):
    id: int
    date: str
    total_cracks: int
    high_severity: int

class BridgeReportsResponse(BaseModel):
    reports: List[InspectionReportBrief]
