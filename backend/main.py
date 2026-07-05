from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import Base, engine, SessionLocal, Bridge, CrackDetection, SensorData, InspectionReport
from mqtt_ingest import start_mqtt_listener
from PIL import Image
import io
import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
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

# WebSocket management
connected_websockets = []

async def broadcast_to_dashboards(payload: dict):
    for ws in list(connected_websockets):
        try:
            await ws.send_json(payload)
        except Exception:
            connected_websockets.remove(ws)

@app.on_event("startup")
async def on_startup():
    start_mqtt_listener(SessionLocal, SensorData, connected_websockets, broadcast_to_dashboards)

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

def send_email_notification(bridge_name, high_severity_count):
    """Send email notification for urgent cracks"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("NOTIFICATION_EMAIL_TO")

    if not all([smtp_host, smtp_user, smtp_password, email_to]):
        print("⚠️ Skipping email notification: missing config")
        return

    subject = f"URGENT: {high_severity_count} High-Severity Cracks Detected on {bridge_name}"
    body = f"""
    Urgent Bridge Crack Notification

    Bridge: {bridge_name}
    High-Severity Cracks Detected: {high_severity_count}
    Time: {datetime.utcnow().isoformat()}

    Please inspect the bridge immediately!
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, email_to, text)
        print(f"✅ Email notification sent to {email_to}")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")

def send_sms_notification(bridge_name, high_severity_count):
    """Send SMS notification for urgent cracks using Twilio"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    sms_to = os.getenv("NOTIFICATION_SMS_TO")

    if not all([account_sid, auth_token, twilio_number, sms_to]):
        print("⚠️ Skipping SMS notification: missing config")
        return

    try:
        client = Client(account_sid, auth_token)
        message_body = f"URGENT: {high_severity_count} high-severity cracks detected on {bridge_name}! Inspect immediately."
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=sms_to
        )
        print(f"✅ SMS notification sent to {sms_to}, SID: {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {str(e)}")

def send_urgent_notifications(bridge_name, high_severity_count):
    """Send both email and SMS notifications for urgent cracks"""
    if high_severity_count > 0:
        send_email_notification(bridge_name, high_severity_count)
        send_sms_notification(bridge_name, high_severity_count)

def generate_crack_identifier(x, y, width, height, threshold=50):
    """Generate a stable identifier for a crack based on position (bucketed)"""
    # Bucket coordinates to make identifier stable despite small position changes
    bucketed_x = round(x / threshold) * threshold
    bucketed_y = round(y / threshold) * threshold
    return f"crack_{bucketed_x}_{bucketed_y}"

def calculate_crack_growth(current_crack, previous_crack):
    """Calculate growth metrics between current and previous crack detection"""
    if not previous_crack:
        return None
    
    area_growth = current_crack.area - previous_crack.area
    area_growth_percent = (area_growth / previous_crack.area) * 100 if previous_crack.area > 0 else 0
    width_growth = current_crack.width - previous_crack.width
    height_growth = current_crack.height - previous_crack.height
    
    return {
        "area_growth": area_growth,
        "area_growth_percent": round(area_growth_percent, 2),
        "width_growth": width_growth,
        "height_growth": height_growth,
        "time_delta_hours": round((current_crack.detected_at - previous_crack.detected_at).total_seconds() / 3600, 2),
        "grew_significantly": area_growth_percent > 10  # Arbitrary threshold for "significant" growth
    }

@app.get("/")
def read_root():
    return {"message": "Bridge Crack Detection Backend is running!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client connected")
    connected_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Just keep the connection open
    except WebSocketDisconnect:
        print("❌ Client disconnected")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

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
        
        saved_cracks = []
        significant_growth_count = 0
        
        for crack_data in cracks:
            # Calculate area and generate crack identifier
            area = crack_data["width"] * crack_data["height"]
            crack_identifier = generate_crack_identifier(
                crack_data["x"], 
                crack_data["y"], 
                crack_data["width"], 
                crack_data["height"]
            )
            
            # Find previous detection of same crack
            previous_crack = db.query(CrackDetection).filter(
                CrackDetection.bridge_id == bridge_id,
                CrackDetection.crack_identifier == crack_identifier
            ).order_by(CrackDetection.detected_at.desc()).first()
            
            # Create new crack detection
            crack = CrackDetection(
                bridge_id=bridge_id,
                x=crack_data["x"],
                y=crack_data["y"],
                width=crack_data["width"],
                height=crack_data["height"],
                area=area,
                confidence=crack_data["confidence"],
                severity_level=crack_data["severity"],
                crack_type=crack_data["crack_type"],
                crack_identifier=crack_identifier,
                previous_crack_id=previous_crack.id if previous_crack else None
            )
            db.add(crack)
            
            # Calculate growth
            if previous_crack:
                growth = calculate_crack_growth(crack, previous_crack)
                if growth and growth["grew_significantly"]:
                    significant_growth_count += 1
                    print(f"⚠️ Significant crack growth detected on {bridge.bridge_name}: {growth}")
            
            saved_cracks.append(crack)
        
        # Calculate high-severity cracks count
        high_severity_count = len([c for c in cracks if c["severity"] >= 3])
        
        # Create inspection report
        report = InspectionReport(
            bridge_id=bridge_id,
            report_date=datetime.now(),
            total_cracks_detected=len(cracks),
            high_severity_cracks=high_severity_count
        )
        db.add(report)
        
        db.commit()
        
        # Send urgent notifications if high-severity cracks or significant growth
        send_urgent_notifications(bridge.bridge_name, high_severity_count)
        if significant_growth_count > 0:
            send_email_notification(
                bridge.bridge_name, 
                f"{significant_growth_count} cracks showing significant growth!"
            )
            send_sms_notification(
                bridge.bridge_name, 
                f"{significant_growth_count} cracks showing significant growth!"
            )
        
        return {
            "message": "Detections saved successfully", 
            "report_id": report.id,
            "significant_growth_count": significant_growth_count
        }
    except Exception as e:
        db.rollback()
        print(f"Error saving detections: {str(e)}")
        return {"error": str(e)}

@app.get("/sensors/data")
async def get_sensor_data(bridge_id: int, limit: int = 7, time_range: str = "30s", db: Session = Depends(get_db)):
    # Calculate cutoff time based on time_range parameter (default 30 seconds)
    if time_range == "30s":
        cutoff_time = datetime.utcnow() - timedelta(seconds=30)
    elif time_range == "1h":
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
    elif time_range == "24h":
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
    else:
        cutoff_time = datetime.utcnow() - timedelta(seconds=30)  # Default to 30s if invalid
    
    results = db.query(SensorData).filter(
        SensorData.bridge_id == bridge_id,
        SensorData.timestamp >= cutoff_time
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
    
    # Calculate cutoff time (30 seconds ago) to avoid stale data
    cutoff_time = datetime.utcnow() - timedelta(seconds=30)
    
    # Filter both cracks and sensor data to only include data from last 30 seconds
    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge_id,
        CrackDetection.detected_at >= cutoff_time
    ).all()
    latest_sensor = db.query(SensorData).filter(
        SensorData.bridge_id == bridge_id,
        SensorData.timestamp >= cutoff_time
    ).order_by(SensorData.timestamp.desc()).first()
    
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

@app.get("/bridge/{bridge_id}/crack-growth")
async def get_crack_growth_history(bridge_id: int, db: Session = Depends(get_db)):
    """Get crack growth history for a bridge, grouped by crack identifier"""
    bridge = db.query(Bridge).filter(Bridge.id == bridge_id).first()
    if not bridge:
        return {"error": "Bridge not found"}
    
    # Get all cracks grouped by crack_identifier
    cracks = db.query(CrackDetection).filter(
        CrackDetection.bridge_id == bridge_id
    ).order_by(CrackDetection.crack_identifier, CrackDetection.detected_at.asc()).all()
    
    # Organize by crack identifier
    crack_history = {}
    for crack in cracks:
        if crack.crack_identifier not in crack_history:
            crack_history[crack.crack_identifier] = []
        
        # Get growth from previous detection if available
        growth = None
        if crack.previous_crack_id:
            previous_crack = db.query(CrackDetection).filter(CrackDetection.id == crack.previous_crack_id).first()
            if previous_crack:
                growth = calculate_crack_growth(crack, previous_crack)
        
        crack_history[crack.crack_identifier].append({
            "id": crack.id,
            "x": crack.x,
            "y": crack.y,
            "width": crack.width,
            "height": crack.height,
            "area": crack.area,
            "confidence": crack.confidence,
            "severity_level": crack.severity_level,
            "crack_type": crack.crack_type,
            "detected_at": crack.detected_at.isoformat(),
            "growth": growth
        })
    
    return {
        "bridge_name": bridge.bridge_name,
        "crack_history": crack_history
    }

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
