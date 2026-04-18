from pydantic import BaseModel
from models.code_submission import SubmissionStatus


class CodeRunRequest(BaseModel):
    question_id: str
    language: str
    code: str


class TestResultResponse(BaseModel):
    test_case_id: str
    passed: bool
    stdout: str
    stderr: str
    runtime_ms: float | None


class CodeRunResponse(BaseModel):
    passed_count: int
    total_count: int
    status: SubmissionStatus
    test_results: list[TestResultResponse]
    submission_id: str | None = None
