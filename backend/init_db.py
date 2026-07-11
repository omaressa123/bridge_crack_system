from database import SessionLocal, init_db
from models import Bridge, CrackDetection, SensorData, InspectionReport
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Cairo bridges with real GIS coordinates
# ─────────────────────────────────────────────
CAIRO_BRIDGES = [
    {"name": "Qasr El-Nile Bridge",  "city": "Cairo", "lat": 30.0459, "lng": 31.2243},
    {"name": "6th October Bridge",   "city": "Cairo", "lat": 30.0571, "lng": 31.2272},
    {"name": "Imbaba Bridge",        "city": "Cairo", "lat": 30.0771, "lng": 31.2089},
]

# Critical area threshold used by predictive maintenance (Feature 2)
# Matches severity_level=3 boundary: width≈150, height≈70 → area≈10500
CRITICAL_AREA_THRESHOLD = 10500


def init_mock_data():
    db = SessionLocal()
    try:
        # ── 1. Create all three Cairo bridges ──────────────────────────────
        bridge_objs = []
        for b in CAIRO_BRIDGES:
            bridge = Bridge(
                bridge_name=b["name"],
                city=b["city"],
                inspection_date=datetime.now(),
                latitude=b["lat"],
                longitude=b["lng"],
            )
            db.add(bridge)
        db.commit()

        # Re-fetch to get IDs
        from models import Bridge as BridgeModel
        bridge_objs = db.query(BridgeModel).all()
        primary_bridge = bridge_objs[0]  # Qasr El-Nile — used for rich seed data

        # ── 2. Sensor history for primary bridge ───────────────────────────
        for i in range(7):
            db.add(SensorData(
                bridge_id=primary_bridge.id,
                temperature_c=32 + i,
                moisture_percent=45 + i,
                acceleration_x=0.8 + (i * 0.01),
                strain_gauge_value=120 + i,
                timestamp=datetime.now() - timedelta(days=6 - i)
            ))

        # ── 3. Generic cracks for primary bridge ───────────────────────────
        for i in range(12):
            db.add(CrackDetection(
                bridge_id=primary_bridge.id,
                x=100 + i * 50,
                y=100 + i * 30,
                width=50 + i * 10,
                height=20 + i * 5,
                area=(50 + i * 10) * (20 + i * 5),
                confidence=0.6 + i * 0.03,
                severity_level=1 if i < 7 else 2 if i < 10 else 3,
                crack_type="hairline" if i < 10 else "structural",
            ))

        db.commit()

        # ── 4. Crack-lineage seed data (Feature 1 demo) ────────────────────
        # Three backdated inspections of the same physical crack, growing over 21 days.
        LINEAGE_ID = "CRK-CAIRO12-001"

        detection_1 = CrackDetection(
            bridge_id=primary_bridge.id,
            x=300, y=200,
            width=60,  height=25,  area=1500,
            confidence=0.72, severity_level=1,
            crack_type="hairline",
            crack_identifier=LINEAGE_ID,
            previous_crack_id=None,
            detected_at=datetime.now() - timedelta(days=21),
        )
        db.add(detection_1)
        db.flush()  # get detection_1.id

        detection_2 = CrackDetection(
            bridge_id=primary_bridge.id,
            x=302, y=201,
            width=90,  height=38,  area=3420,
            confidence=0.81, severity_level=2,
            crack_type="hairline",
            crack_identifier=LINEAGE_ID,
            previous_crack_id=detection_1.id,
            detected_at=datetime.now() - timedelta(days=10),
        )
        db.add(detection_2)
        db.flush()

        detection_3 = CrackDetection(
            bridge_id=primary_bridge.id,
            x=304, y=200,
            width=130, height=62,  area=8060,
            confidence=0.91, severity_level=3,
            crack_type="structural",
            crack_identifier=LINEAGE_ID,
            previous_crack_id=detection_2.id,
            detected_at=datetime.now(),
        )
        db.add(detection_3)

        # ── 5. Cracks for 6th October Bridge (severity 2) ──────────────────
        bridge2 = bridge_objs[1]
        for i in range(5):
            db.add(CrackDetection(
                bridge_id=bridge2.id,
                x=200 + i * 40, y=150 + i * 20,
                width=40 + i * 8, height=18 + i * 4, area=(40 + i * 8) * (18 + i * 4),
                confidence=0.70 + i * 0.04, severity_level=2,
                crack_type="hairline",
                crack_identifier=f"CRK-OCT-00{i+1}",
            ))

        # ── 6. Minor cracks for Imbaba Bridge (severity 1) ─────────────────
        bridge3 = bridge_objs[2]
        for i in range(3):
            db.add(CrackDetection(
                bridge_id=bridge3.id,
                x=100 + i * 60, y=80 + i * 30,
                width=30 + i * 5, height=12 + i * 3, area=(30 + i * 5) * (12 + i * 3),
                confidence=0.65 + i * 0.03, severity_level=1,
                crack_type="hairline",
                crack_identifier=f"CRK-IMB-00{i+1}",
            ))

        # ── 7. Inspection report ───────────────────────────────────────────
        db.add(InspectionReport(
            bridge_id=primary_bridge.id,
            report_date=datetime.now(),
            total_cracks_detected=15,
            high_severity_cracks=2,
        ))

        db.commit()
        print("✅ Mock data (including crack lineage + bridge coordinates) added successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error adding mock data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()  # Create database tables first
    init_mock_data()

