"""Shared application constants."""

# Critical area threshold used by predictive maintenance.
# Matches severity_level=3 boundary: width≈150, height≈70 → area≈10500
CRITICAL_AREA_THRESHOLD = 10500

# Max pixel distance between bounding-box centers to be considered the same crack
CRACK_MATCH_DISTANCE_THRESHOLD = 40

# Bucket size (pixels) for generating default crack identifiers
CRACK_IDENTIFIER_BUCKET_SIZE = 50
