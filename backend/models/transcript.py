from datetime import datetime, timezone
from enum import Enum
from pydantic import Field
from models.base import MongoBase


class Speaker(str, Enum):
    interviewer = "interviewer"
    user = "user"


class TranscriptSegment(MongoBase):
    session_id: str
    question_id: str | None = None
    speaker: Speaker
    text: str
    is_partial: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
