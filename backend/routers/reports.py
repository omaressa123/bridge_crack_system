from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Bridge, InspectionReport
from schemas import BridgeReportsResponse
from services.pdf import generate_inspection_report_pdf

router = APIRouter(
    tags=["reports"],
)


@router.get("/bridge/{bridge_id}/reports", response_model=BridgeReportsResponse)
async def get_bridge_reports(
    bridge_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    reports = db.query(InspectionReport).filter(InspectionReport.bridge_id == bridge_id).all()
    return {
        "reports": [
            {
                "id": r.id,
                "date": r.report_date.isoformat(),
                "total_cracks": r.total_cracks_detected,
                "high_severity": r.high_severity_cracks,
            }
            for r in reports
        ]
    }


@router.get("/report/{report_id}/pdf")
async def get_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    report = db.query(InspectionReport).filter(InspectionReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    bridge = db.query(Bridge).filter(Bridge.id == report.bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=404, detail="Bridge not found for report")

    pdf_buffer = generate_inspection_report_pdf(report, bridge)

    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )
