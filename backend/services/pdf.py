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
