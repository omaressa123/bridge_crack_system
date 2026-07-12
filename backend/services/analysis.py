import logging

logger = logging.getLogger(__name__)


def calculate_overall_severity(cracks, latest_sensor=None):
    """
    Derive overall bridge severity from crack detections.
    Sensor data is reserved for future weighted scoring.
    """
    del latest_sensor  # intentionally unused until sensor-weighted scoring is added

    high_severity = len([c for c in cracks if c.severity_level >= 3])
    if high_severity > 0:
        return 3
    medium_severity = len([c for c in cracks if c.severity_level == 2])
    if medium_severity > 0:
        return 2
    if len(cracks) > 0:
        return 1
    return 0


def get_recommendation(severity):
    if severity == 3:
        return "Immediate Repair Needed"
    if severity == 2:
        return "Monitor Regularly"
    if severity == 1:
        return "No Action Needed"
    return "No Data Available"
