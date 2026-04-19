import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.clerk import require_auth
from db import db
from models.feedback import FeedbackReport
from schemas.feedback import CategoryScoresResponse, EvidenceSpanResponse, FeedbackReportResponse, QuestionFeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


def _require_session_owner(session_id: str, clerk_user_id: str) -> None:
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")


def _report_to_response(doc: dict) -> FeedbackReportResponse:
    report = FeedbackReport.from_mongo(doc)
    return FeedbackReportResponse(
        session_id=report.session_id,
        overall_score=report.overall_score,
        category_scores=CategoryScoresResponse(**report.category_scores.model_dump()),
        per_question_feedback=[
            QuestionFeedbackResponse(
                question_id=qf.question_id,
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
