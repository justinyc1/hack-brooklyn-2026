from datetime import datetime
from pydantic import BaseModel, Field


class CategoryScoresResponse(BaseModel):
    clarity: float | None = None
    confidence: float | None = None
    conciseness: float | None = None
    structure: float | None = None
    specificity: float | None = None
    pace: float | None = None
    problem_solving: float | None = None
    code_correctness: float | None = None
    optimization_awareness: float | None = None
    star_structure: float | None = None
    impact_articulation: float | None = None
    ownership: float | None = None


class EvidenceSpanResponse(BaseModel):
    transcript_segment_id: str
    quote: str
    note: str


class QuestionFeedbackResponse(BaseModel):
    question_id: str
    question_text: str | None = None
    score: float
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    better_answer_example: str | None = None
    evidence: list[EvidenceSpanResponse] = Field(default_factory=list)


class FeedbackReportResponse(BaseModel):
    session_id: str
    overall_score: float
    category_scores: CategoryScoresResponse
    per_question_feedback: list[QuestionFeedbackResponse] = Field(default_factory=list)
    top_strengths: list[str] = Field(default_factory=list)
    top_weaknesses: list[str] = Field(default_factory=list)
    targeted_drills: list[str] = Field(default_factory=list)
    generated_at: datetime


class ReportShareResponse(BaseModel):
    url: str
    expires_in: int
