"""
crack_linking.py
-----------------
Links newly detected cracks to their previous detections on the same bridge
by comparing bounding-box centers. Updates previous_crack_id and crack_identifier
so the history chain stays intact.
"""

import math

from constants import CRACK_IDENTIFIER_BUCKET_SIZE, CRACK_MATCH_DISTANCE_THRESHOLD
from models import CrackDetection


def generate_crack_identifier(x: float, y: float) -> str:
    """Generate a bucketed identifier for a crack position."""
    bucketed_x = round(x / CRACK_IDENTIFIER_BUCKET_SIZE) * CRACK_IDENTIFIER_BUCKET_SIZE
    bucketed_y = round(y / CRACK_IDENTIFIER_BUCKET_SIZE) * CRACK_IDENTIFIER_BUCKET_SIZE
    return f"crack_{bucketed_x}_{bucketed_y}"


def _center(crack):
    return (
        crack.x + crack.width / 2,
        crack.y + crack.height / 2,
    )


def _distance(c1, c2):
    """Euclidean distance between two (x, y) centres."""
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


def link_to_previous_crack(db, bridge_id: int, new_crack: CrackDetection) -> CrackDetection:
    """
    Find the most-recent prior detection of the same physical crack on bridge_id.
    If found, link via previous_crack_id and reuse crack_identifier.
    Otherwise assign a bucketed identifier.
    """
    query = (
        db.query(CrackDetection)
        .filter(CrackDetection.bridge_id == bridge_id)
        .filter(CrackDetection.id != new_crack.id)
    )
    if new_crack.report_id is not None:
        query = query.filter(CrackDetection.report_id != new_crack.report_id)

    prior_detections = query.order_by(CrackDetection.detected_at.desc()).all()

    best_match = None
    best_dist = float("inf")
    new_center = _center(new_crack)

    for prior in prior_detections:
        dist = _distance(new_center, _center(prior))
        if dist < CRACK_MATCH_DISTANCE_THRESHOLD and dist < best_dist:
            best_dist = dist
            best_match = prior

    if best_match:
        new_crack.previous_crack_id = best_match.id
        new_crack.crack_identifier = best_match.crack_identifier
    elif not new_crack.crack_identifier:
        new_crack.crack_identifier = generate_crack_identifier(new_crack.x, new_crack.y)

    return new_crack
