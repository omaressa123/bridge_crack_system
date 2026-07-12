"""Shared crack history logic used by multiple endpoints."""

from sqlalchemy.orm import Session

from models import CrackDetection
from services.prediction import calculate_crack_growth


def build_crack_history(crack_id: int, db: Session) -> dict | None:
    """Build timeline and growth metrics for a crack lineage."""
    timeline = []
    current = db.query(CrackDetection).filter(CrackDetection.id == crack_id).first()
    if not current:
        return None

    visited = set()
    while current and current.id not in visited:
        visited.add(current.id)
        timeline.append(current)
        if current.previous_crack_id:
            current = (
                db.query(CrackDetection)
                .filter(CrackDetection.id == current.previous_crack_id)
                .first()
            )
        else:
            break

    timeline.reverse()
    growth_pct = None
    growth_per_day = None
    if len(timeline) >= 2:
        first, last = timeline[0], timeline[-1]
        if first.area and first.area > 0:
            growth_pct = round((last.area - first.area) / first.area * 100, 1)
        days = (last.detected_at - first.detected_at).total_seconds() / 86400
        if days > 0 and first.area is not None:
            growth_per_day = round((last.area - first.area) / days, 2)

    return {
        "crack_identifier": timeline[0].crack_identifier if timeline else None,
        "inspection_count": len(timeline),
        "growth_pct": growth_pct,
        "growth_per_day": growth_per_day,
        "history": [
            {
                "id": c.id,
                "detected_at": c.detected_at.isoformat(),
                "area": c.area,
                "width": c.width,
                "height": c.height,
                "confidence": c.confidence,
                "severity_level": c.severity_level,
            }
            for c in timeline
        ],
    }
