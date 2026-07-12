import os
import io
import logging
from datetime import datetime, timedelta

from PIL import Image

from constants import CRITICAL_AREA_THRESHOLD

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load YOLO model to avoid blocking startup when weights are missing."""
    global _model
    if _model is None:
        from ultralytics import YOLO

        model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../yolo_model/best1.pt")
        )
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model weights not found at {model_path}")
        _model = YOLO(model_path)
        logger.info("YOLO model loaded from %s", model_path)
    return _model


def classify_severity(confidence: float) -> int:
    if confidence > 0.9:
        return 3
    if confidence > 0.75:
        return 2
    return 1


def detect_cracks_with_yolo(contents: bytes) -> list[dict]:
    img = Image.open(io.BytesIO(contents))
    model = _get_model()
    results = model(img)
    cracks = []

    for result in results:
        for box in result.boxes:
            x_center, y_center, width, height = box.xywh[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            cracks.append({
                "x": x_center,
                "y": y_center,
                "width": width,
                "height": height,
                "confidence": confidence,
                "severity": classify_severity(confidence),
                "crack_type": class_name,
            })
    return cracks


def calculate_crack_growth(current_crack, previous_crack):
    """Calculate growth metrics between current and previous crack detection."""
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
        "time_delta_hours": round(
            (current_crack.detected_at - previous_crack.detected_at).total_seconds() / 3600, 2
        ),
        "grew_significantly": area_growth_percent > 10,
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
