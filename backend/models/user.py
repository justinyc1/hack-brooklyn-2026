from datetime import datetime, timezone
from pydantic import Field
from models.base import MongoBase


class UserPreferences(MongoBase):
    default_difficulty: str = "medium"
    default_duration_minutes: int = 30
    default_interviewer_tone: str = "neutral"


class User(MongoBase):
    clerk_user_id: str
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    preferences: UserPreferences = Field(default_factory=UserPreferences)
