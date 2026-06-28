from models import SessionLocal, Bridge, CrackDetection, SensorData, InspectionReport
from datetime import datetime, timedelta

def init_mock_data():
    db = SessionLocal()
    try:
        bridge = Bridge(
            bridge_name="Qasr El-Nile Bridge",
            city="Cairo",
            inspection_date=datetime.now()
        )
        db.add(bridge)
        db.commit()
        db.refresh(bridge)
        
        for i in range(7):
            sensor_data = SensorData(
                bridge_id=bridge.id,
                temperature_c=32 + i,
                moisture_percent=45 + i,
                acceleration_x=0.8 + (i * 0.01),
                strain_gauge_value=120 + i,
                timestamp=datetime.now() - timedelta(days=6 - i)
            )
            db.add(sensor_data)
        
        for i in range(12):
            crack = CrackDetection(
                bridge_id=bridge.id,
                x=100 + i * 50,
                y=100 + i * 30,
                width=50 + i * 10,
                height=20 + i * 5,
                confidence=0.6 + i * 0.03,
                severity_level=1 if i < 7 else 2 if i < 10 else 3,
                crack_type="hairline" if i < 10 else "structural"
            )
            db.add(crack)
        
        report = InspectionReport(
            bridge_id=bridge.id,
            report_date=datetime.now(),
            total_cracks_detected=12,
            high_severity_cracks=2
        )
        db.add(report)
        
        db.commit()
        print("✅ Mock data added successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error adding mock data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_mock_data()
