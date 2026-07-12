from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_inspection_report_pdf(report, bridge):
    """
    Generates a PDF report for a bridge inspection.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Bridge Inspection Report")
    
    # Details
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Date: {report.report_date}")
    c.drawString(100, 710, f"Bridge: {bridge.bridge_name}")
    c.drawString(100, 690, f"City: {bridge.city}")
    c.drawString(100, 670, f"Total Cracks Detected: {report.total_cracks_detected}")
    c.drawString(100, 650, f"High Severity Cracks: {report.high_severity_cracks}")
    
    if report.model_version:
        c.drawString(100, 630, f"YOLO Model Version: {report.model_version}")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer


def generate_inspection_pdf(reports, output_path: str = "uploads/inspection_report.pdf"):
    """Generate a fleet-level inspection PDF from multiple reports."""
    from pathlib import Path

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Fleet Inspection Report")
    c.setFont("Helvetica", 10)
    y = 720
    for report in reports[:40]:
        bridge = getattr(report, "bridge", None)
        bridge_name = bridge.bridge_name if bridge else f"Bridge #{report.bridge_id}"
        line = (
            f"{report.report_date.strftime('%Y-%m-%d')} | {bridge_name} | "
            f"cracks={report.total_cracks_detected} high={report.high_severity_cracks}"
        )
        c.drawString(60, y, line[:90])
        y -= 16
        if y < 60:
            c.showPage()
            y = 750
    c.save()
    out.write_bytes(buffer.getvalue())
    return str(out)
