from datetime import datetime
from pydantic import BaseModel, Field
from models.interview_session import Difficulty, InterviewMode, InterviewerTone, SessionStatus


class CreateSessionRequest(BaseModel):
    mode: InterviewMode
    role: str
    company: str | None = None
    difficulty: Difficulty = Difficulty.medium
    duration_minutes: int = Field(default=30, ge=5, le=120)
    interviewer_tone: InterviewerTone = InterviewerTone.neutral


class PatchSessionRequest(BaseModel):
    status: SessionStatus | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class SessionResponse(BaseModel):
    id: str
    clerk_user_id: str
    mode: InterviewMode
    role: str
    company: str | None
    difficulty: Difficulty
    duration_minutes: int
    interviewer_tone: InterviewerTone
    status: SessionStatus
    question_ids: list[str]
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
