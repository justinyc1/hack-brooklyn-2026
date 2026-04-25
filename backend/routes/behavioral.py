import logging

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from auth.clerk import require_auth
from db import db
from models.interview_session import InterviewMode, InterviewSession
from routes._helpers import session_to_response
from schemas.interviews import CreateBehavioralSessionRequest, SessionResponse
from services.elevenlabs import create_behavioral_agent
from services.tts_cache import prewarm as tts_prewarm
from services.question_planner import plan_behavioral_questions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interviews/behavioral", tags=["behavioral"])


from auth.rate_limit import RateLimiter

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_behavioral_session(
    body: CreateBehavioralSessionRequest,
    background_tasks: BackgroundTasks,
    clerk_user_id: str = Depends(RateLimiter(5, 60, "create_behavioral_session")),
):
    session = InterviewSession(
        clerk_user_id=clerk_user_id,
        mode=InterviewMode.behavioral,
        behavioral_persona=body.behavioral_persona,
        duration_minutes=body.duration_minutes,
    )

    result = db.sessions.insert_one(session.to_mongo())
    session_id = str(result.inserted_id)
    session.id = session_id

    try:
        questions = await plan_behavioral_questions(session_id, body.duration_minutes)
    except Exception as exc:
        db.sessions.delete_one({"_id": result.inserted_id})
        logger.error("Question generation failed for behavioral session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate interview questions. Please try again.",
        )

    question_ids: list[str] = []
    if questions:
        q_docs = [q.to_mongo() for q in questions]
        q_result = db.questions.insert_many(q_docs)
        question_ids = [str(qid) for qid in q_result.inserted_ids]

    agent_id: str | None = None
    try:
        agent_id, first_msg, voice_cfg = await create_behavioral_agent(session, questions)
        background_tasks.add_task(
            tts_prewarm,
            first_msg,
            voice_cfg["voice_id"],
            voice_cfg["stability"],
            voice_cfg["similarity_boost"],
        )
    except Exception as exc:
        logger.error("ElevenLabs agent creation failed for behavioral session %s: %s", session_id, exc)

    db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"question_ids": question_ids, "elevenlabs_agent_id": agent_id}},
    )

    doc = db.sessions.find_one({"_id": ObjectId(session_id)})
    return session_to_response(doc)
