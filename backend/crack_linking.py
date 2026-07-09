"""
crack_linking.py
-----------------
Links newly detected cracks to their previous detections on the same bridge
by comparing bounding-box centers. Updates previous_crack_id and crack_identifier
so the history chain stays intact.
"""

from models import CrackDetection
import math


# Max pixel distance between bounding-box centers to be considered the same crack
MATCH_DISTANCE_THRESHOLD = 80  # pixels


def _center(crack):
    """Return (cx, cy) of a CrackDetection."""
    return crack.x, crack.y


def _distance(c1, c2):
    """Euclidean distance between two (x, y) centres."""
    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


def link_to_previous_crack(db, bridge_id: int, new_crack: CrackDetection) -> CrackDetection:
    """
    Try to find the most-recent prior detection of the same physical crack on
    bridge_id.  If found:
      - set new_crack.previous_crack_id -> prior detection id
      - copy prior detection crack_identifier so the whole lineage shares one ID

    Returns new_crack modified in-place (not yet flushed/committed).
    """
    prior_detections = (
        db.query(CrackDetection)
        .filter(CrackDetection.bridge_id == bridge_id)
        .order_by(CrackDetection.detected_at.desc())
        .all()
    )

    best_match = None
    best_dist = float("inf")
    new_center = _center(new_crack)

    for prior in prior_detections:
        dist = _distance(new_center, _center(prior))
        if dist < MATCH_DISTANCE_THRESHOLD and dist < best_dist:
            best_dist = dist
            best_match = prior

    if best_match:
        new_crack.previous_crack_id = best_match.id
        new_crack.crack_identifier = best_match.crack_identifier

    return new_crack
