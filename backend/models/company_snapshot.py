from datetime import datetime, timezone
from pydantic import Field
from models.base import MongoBase


class ThemeScore(MongoBase):
    theme: str
    confidence: float


class CompanySnapshot(MongoBase):
    company: str
    role: str | None = None
    behavioral_themes: list[ThemeScore] = Field(default_factory=list)
    technical_focus: list[ThemeScore] = Field(default_factory=list)
    style_signals: list[ThemeScore] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
