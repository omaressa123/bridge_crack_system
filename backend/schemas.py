from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GoogleLoginRequest(BaseModel):
    credential: str

class GoogleLoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]

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

class CrackDetectResponse(BaseModel):
    cracks: List[CrackBase] = Field(default_factory=list)
    error: Optional[str] = None

class CrackSaveResponse(BaseModel):
    message: Optional[str] = None
    report_id: Optional[int] = None
    significant_growth_count: Optional[int] = None
    saved_crack_ids: Optional[List[int]] = None
    error: Optional[str] = None

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

class BridgeMapItem(BaseModel):
    id: int
    name: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    max_severity: int
    total_cracks: int
    high_severity_cracks: int
    recommendation: str

class BridgeMapResponse(BaseModel):
    bridges: List[BridgeMapItem]

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

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
