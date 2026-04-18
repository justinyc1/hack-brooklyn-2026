from datetime import datetime, timezone
from pydantic import Field
from models.base import MongoBase


class EvidenceSpan(MongoBase):
    transcript_segment_id: str
    quote: str
    note: str


class CategoryScores(MongoBase):
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


class QuestionFeedback(MongoBase):
    question_id: str
    score: float
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    better_answer_example: str | None = None
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class FeedbackReport(MongoBase):
    session_id: str
    overall_score: float
    category_scores: CategoryScores
    per_question_feedback: list[QuestionFeedback] = Field(default_factory=list)
    top_strengths: list[str] = Field(default_factory=list)
    top_weaknesses: list[str] = Field(default_factory=list)
    targeted_drills: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
