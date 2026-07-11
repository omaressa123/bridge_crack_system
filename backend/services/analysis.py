def calculate_overall_severity(cracks, latest_sensor):
    high_severity = len([c for c in cracks if c.severity_level >= 3])
    if high_severity > 0:
        return 3
    medium_severity = len([c for c in cracks if c.severity_level == 2])
    if medium_severity > 0:
        return 2
    return 1

def get_recommendation(severity):
    if severity == 3:
        return "Immediate Repair Needed"
    elif severity == 2:
        return "Monitor Regularly"
    else:
        return "No Action Needed"
