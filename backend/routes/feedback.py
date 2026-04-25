import logging

from botocore.exceptions import ClientError
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.clerk import require_auth
from db import db
from models.feedback import FeedbackReport
from models.interview_session import InterviewSession
from schemas.feedback import (
    CategoryScoresResponse,
    EvidenceSpanResponse,
    FeedbackReportResponse,
    QuestionFeedbackResponse,
    ReportShareResponse,
)
from services.report_generator import generate_feedback_html
from services.s3 import BUCKET_NAME, generate_presigned_url, s3_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

_SHARE_EXPIRY = 604800  # 7 days in seconds


def _require_session_owner(session_id: str, clerk_user_id: str) -> dict:
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return doc


def _report_to_response(doc: dict) -> FeedbackReportResponse:
    report = FeedbackReport.from_mongo(doc)
    return FeedbackReportResponse(
        session_id=report.session_id,
        overall_score=report.overall_score,
        category_scores=CategoryScoresResponse(**report.category_scores.model_dump()),
        per_question_feedback=[
            QuestionFeedbackResponse(
                question_id=qf.question_id,
                question_text=qf.question_text,
                score=qf.score,
                strengths=qf.strengths,
                improvements=qf.improvements,
                better_answer_example=qf.better_answer_example,
                evidence=[
                    EvidenceSpanResponse(
                        transcript_segment_id=e.transcript_segment_id,
                        quote=e.quote,
                        note=e.note,
                    )
                    for e in qf.evidence
                ],
            )
            for qf in report.per_question_feedback
        ],
        top_strengths=report.top_strengths,
        top_weaknesses=report.top_weaknesses,
        targeted_drills=report.targeted_drills,
        generated_at=report.generated_at,
    )


@router.get("/demo", response_model=FeedbackReportResponse)
def get_demo_feedback():
    """Public endpoint — returns the seeded demo feedback report, no auth required."""
    doc = db.feedback.find_one({"session_id": "demo"})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo feedback not found. Run scripts/seed_demo.py.",
        )
    return _report_to_response(doc)


@router.get("/{session_id}", response_model=FeedbackReportResponse)
def get_feedback(
    session_id: str,
    clerk_user_id: str = Depends(require_auth),
):
    _require_session_owner(session_id, clerk_user_id)

    doc = db.feedback.find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not yet generated. Try again shortly.",
        )

    return _report_to_response(doc)


@router.post("/{session_id}/share", response_model=ReportShareResponse)
def share_feedback_report(
    session_id: str,
    clerk_user_id: str = Depends(require_auth),
):
    """Generate an HTML feedback report, upload to S3, return a 7-day presigned URL."""
    session_doc = _require_session_owner(session_id, clerk_user_id)

    feedback_doc = db.feedback.find_one({"session_id": session_id})
    if not feedback_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not yet generated. Try again shortly.",
        )

    report = FeedbackReport.from_mongo(feedback_doc)

    if not report.report_s3_key:
        session = InterviewSession.from_mongo(session_doc)
        html = generate_feedback_html(report, session)
        s3_key = f"reports/{session_id}/feedback.html"
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=html.encode("utf-8"),
                ContentType="text/html; charset=utf-8",
            )
        except ClientError as exc:
            logger.error("Failed to upload report HTML to S3 (%s): %s", s3_key, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate report",
            )
        db.feedback.update_one({"session_id": session_id}, {"$set": {"report_s3_key": s3_key}})
        report.report_s3_key = s3_key

    url = generate_presigned_url(report.report_s3_key, expiration=_SHARE_EXPIRY)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate share URL",
        )

    return ReportShareResponse(url=url, expires_in=_SHARE_EXPIRY)
