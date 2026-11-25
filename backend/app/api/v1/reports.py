from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.schemas.report import ReportResponse, FindingResponse
from backend.app.schemas.feedback import FeedbackCreate, FeedbackResponse
from backend.app.models.report import Report
from backend.app.models.feedback import Feedback
from backend.app.db.session import get_db
from backend.app.api.v1.analyze import build_what_to_do_next

router = APIRouter()


@router.get("/reports/{report_id}", response_model=ReportResponse, tags=["Reports"])
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full audit report, calculated risk score, findings, and recommendations."""
    stmt = (
        select(Report)
        .options(selectinload(Report.findings))
        .where(Report.id == report_id)
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id '{report_id}' not found."
        )

    findings_list = [
        FindingResponse(
            id=f.id,
            report_id=f.report_id,
            rule_id=f.rule_id,
            weight=f.weight,
            confidence=f.confidence,
            evidence=f.evidence
        )
        for f in report.findings
    ]

    what_next = build_what_to_do_next(report.verdict)

    return ReportResponse(
        id=report.id,
        created_at=report.created_at,
        sender_domain=report.sender_domain,
        company=report.company,
        score=report.score,
        verdict=report.verdict,
        status=report.status,
        redacted_text=report.redacted_text,
        findings=findings_list,
        what_to_do_next=what_next
    )


@router.post("/reports/{report_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED, tags=["Feedback"])
async def submit_feedback(
    report_id: str,
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit user feedback ('real' | 'scam') to calibrate OfferCheck detection."""
    # Verify report exists
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id '{report_id}' not found."
        )

    feedback_entry = Feedback(
        report_id=report_id,
        label=payload.label,
        note=payload.note
    )
    db.add(feedback_entry)
    await db.commit()
    await db.refresh(feedback_entry)

    return FeedbackResponse(
        id=feedback_entry.id,
        report_id=feedback_entry.report_id,
        label=feedback_entry.label,
        note=feedback_entry.note,
        created_at=feedback_entry.created_at
    )
