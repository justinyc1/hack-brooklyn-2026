from datetime import datetime, timezone
from enum import Enum
from pydantic import Field
from models.base import MongoBase


class InterviewMode(str, Enum):
    technical = "technical"
    behavioral = "behavioral"
    mixed = "mixed"
    resume = "resume"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class InterviewerTone(str, Enum):
    friendly = "friendly"
    neutral = "neutral"
    intense = "intense"
    skeptical = "skeptical"


class BehavioralPersona(str, Enum):
    supportive = "supportive"
    corporate = "corporate"
    pressure = "pressure"
    probing = "probing"


class SessionStatus(str, Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    abandoned = "abandoned"


class InterviewSession(MongoBase):
    clerk_user_id: str
    mode: InterviewMode
    role: str | None = None
    company: str | None = None
    difficulty: Difficulty | None = None
    duration_minutes: int = 30
    interviewer_tone: InterviewerTone | None = None
    behavioral_persona: BehavioralPersona | None = None
    status: SessionStatus = SessionStatus.pending
    company_snapshot_id: str | None = None
    resume_text: str | None = None
    resume_s3_url: str | None = None
    audio_s3_url: str | None = None
    question_ids: list[str] = Field(default_factory=list)
    elevenlabs_agent_id: str | None = None
    elevenlabs_conversation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    ended_at: datetime | None = None
