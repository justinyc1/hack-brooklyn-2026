from datetime import datetime, timezone
from enum import Enum
from pydantic import Field
from models.base import MongoBase


class SubmissionStatus(str, Enum):
    accepted = "accepted"
    wrong_answer = "wrong_answer"
    runtime_error = "runtime_error"
    time_limit_exceeded = "time_limit_exceeded"
    compile_error = "compile_error"


class TestResult(MongoBase):
    test_case_id: str
    passed: bool
    stdout: str = ""
    stderr: str = ""
    runtime_ms: float | None = None


class CodeSubmission(MongoBase):
    session_id: str
    question_id: str
    language: str
    code: str
    is_final: bool = False
    status: SubmissionStatus | None = None
    passed_count: int = 0
    total_count: int = 0
    test_results: list[TestResult] = Field(default_factory=list)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
