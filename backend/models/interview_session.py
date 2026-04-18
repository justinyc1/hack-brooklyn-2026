from datetime import datetime, timezone
from enum import Enum
from pydantic import Field
from models.base import MongoBase


class InterviewMode(str, Enum):
    technical = "technical"
    behavioral = "behavioral"
    mixed = "mixed"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class InterviewerTone(str, Enum):
    friendly = "friendly"
    neutral = "neutral"
    intense = "intense"
    skeptical = "skeptical"


class SessionStatus(str, Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    abandoned = "abandoned"


class InterviewSession(MongoBase):
    clerk_user_id: str
    mode: InterviewMode
    role: str
    company: str | None = None
    difficulty: Difficulty = Difficulty.medium
    duration_minutes: int = 30
    interviewer_tone: InterviewerTone = InterviewerTone.neutral
    status: SessionStatus = SessionStatus.pending
    company_snapshot_id: str | None = None
    question_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    ended_at: datetime | None = None
