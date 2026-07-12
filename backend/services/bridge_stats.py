"""Bridge-level aggregation queries shared across API endpoints."""

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from models import CrackDetection


def get_bridge_crack_stats(db: Session, bridge_ids: list[int] | None = None) -> dict[int, dict]:
    """Return crack count, max severity, and high-severity count per bridge."""
    high_severity_case = case(
        (CrackDetection.severity_level >= 3, 1),
        else_=0,
    )
    query = db.query(
        CrackDetection.bridge_id,
        func.count(CrackDetection.id).label("total_cracks"),
        func.max(CrackDetection.severity_level).label("max_severity"),
        func.sum(high_severity_case).label("high_severity_cracks"),
    ).group_by(CrackDetection.bridge_id)

    if bridge_ids is not None:
        query = query.filter(CrackDetection.bridge_id.in_(bridge_ids))

    stats: dict[int, dict] = {}
    for row in query.all():
        stats[row.bridge_id] = {
            "total_cracks": int(row.total_cracks or 0),
            "max_severity": int(row.max_severity or 0),
            "high_severity_cracks": int(row.high_severity_cracks or 0),
        }
    return stats
