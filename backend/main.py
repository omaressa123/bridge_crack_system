from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Base, engine, SessionLocal, Bridge, CrackDetection, SensorData, InspectionReport
from PIL import Image
import io
import asyncio
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from ultralytics import YOLO
import os

app = FastAPI()

# Load the YOLO model once at startup
model_path = os.path.join(os.path.dirname(__file__), "../yolo_model", "best1.pt")
model = YOLO(model_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def classify_severity(confidence):
    if confidence > 0.9:
        return 3
    elif confidence > 0.75:
        return 2
    else:
        return 1

def calculate_overall_severity(cracks, latest_sensor):
    high_severity = len([c for c in cracks if c.severity_level >= 3])
    if high_severity > 0:
        return 3
    medium_severity = len([c for c in cracks if c.severity_level == 2])
    if medium_severity > 0:
        return 2
    return 1

def get_recommendation(severity):
    if severity == 3:
        return "Immediate Repair Needed"
    elif severity == 2:
        return "Monitor Regularly"
    else:
        return "No Action Needed"

@app.get("/")
def read_root():
    return {"message": "Bridge Crack Detection Backend is running!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Mobile app connected")
    try:
        while True:
            sensor_data = {
                "temperature": 32,
                "moisture": 45,
                "vibration": 0.8,
                "strain": 120,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(sensor_data)
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        print("❌ Mobile app disconnected")

@app.post("/detect")
async def detect_cracks(image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        
        # Run YOLO detection
        results = model(img)
        
        cracks = []
        
        # Process results
        for result in results:
            for box in result.boxes:
                # Get box coordinates (xywh format: x_center, y_center, width, height)
                x_center, y_center, width, height = box.xywh[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                
                crack = {
                    "x": x_center,
                    "y": y_center,
                    "width": width,
                    "height": height,
                    "confidence": confidence,
                    "severity": classify_severity(confidence),
                    "crack_type": class_name
                }
                cracks.append(crack)
        
        return {"cracks": cracks}
    except Exception as e:
        print(f"Detection error: {str(e)}")
        return {"error": str(e), "cracks": []}

# Endpoint to save detections to database
@app.post("/detect/{bridge_id}/save")
async def save_detections(bridge_id: int, cracks: list[dict], db: Session = Depends(get_db)):
    try:
        bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
        if not bridge:
            return {"error": "Bridge not found"}
        
        for crack_data in cracks:
            crack = CrackDetection(
                bridge_id=bridge_id,
                x=crack_data["x"],
                y=crack_data["y"],
                width=crack_data["width"],
                height=crack_data["height"],
                confidence=crack_data["confidence"],
                severity_level=crack_data["severity"],
                crack_type=crack_data["crack_type"]
            )
            db.add(crack)
        
        # Create inspection report
        report = InspectionReport(
            bridge_id=bridge_id,
            report_date=datetime.now(),
            total_cracks_detected=len(cracks),
            high_severity_cracks=len([c for c in cracks if c["severity"] >= 3])
        )
        db.add(report)
        
        db.commit()
        
        return {"message": "Detections saved successfully", "report_id": report.id}
    except Exception as e:
        db.rollback()
        print(f"Error saving detections: {str(e)}")
        return {"error": str(e)}

@app.get("/sensors/data")
async def get_sensor_data(bridge_id: int, limit: int = 7, time_range: str = "24h", db: Session = Depends(get_db)):
    results = db.query(SensorData).filter(
        SensorData.bridge_id == bridge_id
    ).order_by(
        SensorData.timestamp.desc()
    ).limit(limit).all()
    results = list(reversed(results))
    
    if not results:
        # If no data in DB, return empty arrays instead of mock data
        return {
            "temperature_history": [],
            "moisture_history": [],
            "vibration_history": [],
            "strain_history": [],
            "timestamps": []
        }
    
    return {
        "temperature_history": [r.temperature_c for r in results],
        "moisture_history": [r.moisture_percent for r in results],
        "vibration_history": [r.acceleration_x for r in results],
        "strain_history": [r.strain_gauge_value for r in results],
        "timestamps": [r.timestamp.isoformat() for r in results]
    }

@app.get("/bridge/{bridge_id}/status")
async def get_bridge_status(bridge_id: int, db: Session = Depends(get_db)):
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        # If bridge not found, return 404
        return {"error": "Bridge not found"}
    
    cracks = db.query(CrackDetection).filter(CrackDetection.bridge_id == bridge_id).all()
    latest_sensor = db.query(SensorData).filter(SensorData.bridge_id == bridge_id).order_by(SensorData.timestamp.desc()).first()
    
    if not latest_sensor:
        return {"error": "No sensor data available for this bridge"}
    
    severity = calculate_overall_severity(cracks, latest_sensor)
    
    return {
        "bridge_name": bridge.bridge_name,
        "city": bridge.city,
        "overall_severity": severity,
        "total_cracks": len(cracks),
        "high_severity_cracks": len([c for c in cracks if c.severity_level >= 3]),
        "last_inspection_date": bridge.inspection_date.isoformat(),
        "recommendation": get_recommendation(severity),
        "current_sensors": {
            "temperature": latest_sensor.temperature_c,
            "moisture": latest_sensor.moisture_percent,
            "vibration": latest_sensor.acceleration_x,
            "strain": latest_sensor.strain_gauge_value
        }
    }

# Get list of bridges
@app.get("/bridges")
async def get_bridges(db: Session = Depends(get_db)):
    bridges = db.query(Bridge).all()
    return {"bridges": [{"id": b.id, "name": b.bridge_name, "city": b.city} for b in bridges]}

# Get all inspection reports for a bridge
@app.get("/bridge/{bridge_id}/reports")
async def get_bridge_reports(bridge_id: int, db: Session = Depends(get_db)):
    reports = db.query(InspectionReport).filter(InspectionReport.bridge_id == bridge_id).all()
    return {"reports": [{"id": r.id, "date": r.report_date.isoformat(), "total_cracks": r.total_cracks_detected, "high_severity": r.high_severity_cracks} for r in reports]}

@app.get("/report/{report_id}/pdf")
async def get_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(InspectionReport).filter(InspectionReport.id == report_id).first()
    if not report:
        return {"error": "Report not found"}
    
    bridge = db.query(Bridge).filter(Bridge.id == report.bridge_id).first()
    if not bridge:
        return {"error": "Bridge not found for report"}
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Bridge Inspection Report")
    c.drawString(100, 730, f"Date: {report.report_date}")
    c.drawString(100, 710, f"Bridge: {bridge.bridge_name}")
    c.drawString(100, 690, f"Total Cracks: {report.total_cracks_detected}")
    c.drawString(100, 670, f"High Severity: {report.high_severity_cracks}")
    c.save()
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
