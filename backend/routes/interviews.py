from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.clerk import require_auth
from db import db
from models.interview_session import InterviewSession, SessionStatus
from models.question import Question
from schemas.interviews import (
    CreateSessionRequest,
    PatchSessionRequest,
    SessionListResponse,
    SessionResponse,
)
from services.question_planner import plan_questions

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


def _session_to_response(doc: dict) -> SessionResponse:
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
        status=session.status,
        question_ids=session.question_ids,
        created_at=session.created_at,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    clerk_user_id: str = Depends(require_auth),
):

    session = InterviewSession(
        clerk_user_id=clerk_user_id,
        mode=body.mode,
        role=body.role,
        company=body.company,
        difficulty=body.difficulty,
        duration_minutes=body.duration_minutes,
        interviewer_tone=body.interviewer_tone,
    )

    result = db.sessions.insert_one(session.to_mongo())
    session_id = str(result.inserted_id)

    questions: list[Question] = plan_questions(session_id, body.mode, body.role)
    question_ids: list[str] = []
    if questions:
        q_docs = [q.to_mongo() for q in questions]
        q_result = db.questions.insert_many(q_docs)
        question_ids = [str(qid) for qid in q_result.inserted_ids]

    db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"question_ids": question_ids}},
    )

    doc = db.sessions.find_one({"_id": ObjectId(session_id)})
    return _session_to_response(doc)


@router.get("", response_model=SessionListResponse)
def list_sessions(clerk_user_id: str = Depends(require_auth)):

    docs = list(db.sessions.find({"clerk_user_id": clerk_user_id}).sort("created_at", -1))
    sessions = [_session_to_response(d) for d in docs]
    return SessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    clerk_user_id: str = Depends(require_auth),
):

    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")

    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return _session_to_response(doc)


@router.patch("/{session_id}", response_model=SessionResponse)
def patch_session(
    session_id: str,
    body: PatchSessionRequest,
    clerk_user_id: str = Depends(require_auth),
):

    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")

    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    updates: dict = {}
    if body.status is not None:
        updates["status"] = body.status.value
        if body.status == SessionStatus.active and not doc.get("started_at"):
            updates["started_at"] = datetime.now(timezone.utc)
        if body.status == SessionStatus.completed and not doc.get("ended_at"):
            updates["ended_at"] = datetime.now(timezone.utc)
    if body.started_at is not None:
        updates["started_at"] = body.started_at
    if body.ended_at is not None:
        updates["ended_at"] = body.ended_at

    if updates:
        db.sessions.update_one({"_id": ObjectId(session_id)}, {"$set": updates})

    doc = db.sessions.find_one({"_id": ObjectId(session_id)})
    return _session_to_response(doc)
