from datetime import datetime
from pydantic import BaseModel, Field


class ThemeScoreResponse(BaseModel):
    theme: str
    confidence: float


class CompanySnapshotResponse(BaseModel):
    company: str
    role: str | None = None
    behavioral_themes: list[ThemeScoreResponse] = Field(default_factory=list)
    technical_focus: list[ThemeScoreResponse] = Field(default_factory=list)
    style_signals: list[ThemeScoreResponse] = Field(default_factory=list)
    retrieved_at: datetime
    is_fresh: bool = False
