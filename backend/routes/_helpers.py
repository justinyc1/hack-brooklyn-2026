"""Shared route helpers used by both interviews and behavioral routers."""

from models.interview_session import InterviewSession
from schemas.interviews import SessionResponse


def session_to_response(doc: dict) -> SessionResponse:
    session = InterviewSession.from_mongo(doc)
    return SessionResponse(
        id=session.id,
        clerk_user_id=session.clerk_user_id,
        mode=session.mode,
        role=session.role,
        company=session.company,
        difficulty=session.difficulty,
        duration_minutes=session.duration_minutes,
        interviewer_tone=session.interviewer_tone,
        behavioral_persona=session.behavioral_persona,
        status=session.status,
        question_ids=session.question_ids,
        elevenlabs_agent_id=session.elevenlabs_agent_id,
        elevenlabs_conversation_id=session.elevenlabs_conversation_id,
        created_at=session.created_at,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )
