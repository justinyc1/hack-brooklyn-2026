from datetime import datetime
from pydantic import BaseModel
from models.transcript import Speaker


class AddSegmentRequest(BaseModel):
    speaker: Speaker
    text: str
    is_partial: bool = False
    question_id: str | None = None


class SegmentResponse(BaseModel):
    id: str
    session_id: str
    question_id: str | None
    speaker: Speaker
    text: str
    is_partial: bool
    timestamp: datetime


class TranscriptResponse(BaseModel):
    session_id: str
    segments: list[SegmentResponse]
    total: int


class TranscriptByQuestionResponse(BaseModel):
    session_id: str
    by_question: dict[str, list[SegmentResponse]]
    unattributed: list[SegmentResponse]
