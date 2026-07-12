from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from deps import get_bridge_or_404, get_current_active_user
from database import get_db
from models import Bridge, InspectionReport
from schemas import BridgeReportsResponse, ReportSortField, SortOrder
from services.pdf import generate_inspection_report_pdf

router = APIRouter(
    tags=["reports"],
)


@router.get("/bridge/{bridge_id}/reports", response_model=BridgeReportsResponse)
async def get_bridge_reports(
    bridge: Bridge = Depends(get_bridge_or_404),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Max reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    sort: ReportSortField = Query(ReportSortField.date),
    order: SortOrder = Query(SortOrder.desc),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    sort_column = {
        ReportSortField.date: InspectionReport.report_date,
        ReportSortField.total_cracks: InspectionReport.total_cracks_detected,
        ReportSortField.high_severity: InspectionReport.high_severity_cracks,
    }[sort]

    query = db.query(InspectionReport).filter(InspectionReport.bridge_id == bridge.id)
    total = query.count()

    if order == SortOrder.desc:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    if limit is not None:
        query = query.offset(offset).limit(limit)
    elif offset:
        query = query.offset(offset)

    reports = query.all()
    return {
        "reports": [
            {
                "id": r.id,
                "date": r.report_date.isoformat(),
                "total_cracks": r.total_cracks_detected,
                "high_severity": r.high_severity_cracks,
            }
            for r in reports
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/report/{report_id}/pdf")
async def get_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    report = db.query(InspectionReport).filter(InspectionReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    bridge = db.query(Bridge).filter(Bridge.id == report.bridge_id).first()
    if not bridge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bridge not found for report")

    pdf_buffer = generate_inspection_report_pdf(report, bridge)

    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )
