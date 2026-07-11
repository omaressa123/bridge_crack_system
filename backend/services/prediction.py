import os
import io
import math
from datetime import datetime, timedelta
from ultralytics import YOLO
from PIL import Image

CRITICAL_AREA_THRESHOLD = 10500

# Absolute path resolution to find the YOLO model weight relative to this file
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolo_model/best1.pt"))
model = YOLO(model_path)

def classify_severity(confidence: float) -> int:
    if confidence > 0.9:
        return 3
    elif confidence > 0.75:
        return 2
    else:
        return 1

def detect_cracks_with_yolo(contents: bytes) -> list[dict]:
    img = Image.open(io.BytesIO(contents))
    results = model(img)
    cracks = []
    
    for result in results:
        for box in result.boxes:
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
    return cracks

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

def predict_crack_maintenance(history: list, growth_per_day: float) -> dict:
    """
    Linear extrapolation of crack growth to estimate when the crack will
    reach CRITICAL_AREA_THRESHOLD. Returns bilingual messages.
    """
    if len(history) < 2:
        return {
            "status": "insufficient_data",
            "message_en": "Not enough inspection history to make a prediction (need ≥ 2 inspections).",
            "message_ar": "لا توجد بيانات كافية للتنبؤ (يلزم فحصان على الأقل).",
            "recommended_inspection_date": None,
        }

    current_area = history[-1]["area"] or 0

    if current_area >= CRITICAL_AREA_THRESHOLD:
        return {
            "status": "critical_now",
            "message_en": "⚠️ Crack has already reached critical size. Immediate inspection required.",
            "message_ar": "⚠️ وصل الشرخ إلى الحجم الحرج. الفحص الفوري مطلوب.",
            "recommended_inspection_date": datetime.now().date().isoformat(),
        }

    if growth_per_day <= 0:
        return {
            "status": "no_trend",
            "message_en": "No growth trend detected — crack appears stable. Continue routine monitoring.",
            "message_ar": "لا يوجد اتجاه نمو — الشرخ يبدو مستقراً. استمر في المراقبة الدورية.",
            "recommended_inspection_date": None,
        }

    days_to_critical = (CRITICAL_AREA_THRESHOLD - current_area) / growth_per_day
    inspection_date = (datetime.now() + timedelta(days=days_to_critical)).date()
    days_int = int(round(days_to_critical))

    return {
        "status": "active_growth",
        "days_to_critical": days_int,
        "current_area": current_area,
        "growth_per_day": growth_per_day,
        "message_en": f"~{days_int} days to critical size — recommend inspection by {inspection_date}.",
        "message_ar": f"~{days_int} يوماً حتى الحجم الحرج — يُوصى بالفحص بحلول {inspection_date}.",
        "recommended_inspection_date": inspection_date.isoformat(),
    }
