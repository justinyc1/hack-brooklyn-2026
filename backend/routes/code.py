from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.clerk import require_auth
from db import db
from models.code_submission import CodeSubmission, SubmissionStatus, TestResult
from schemas.code import CodeRunRequest, CodeRunResponse, TestResultResponse
from services.code_runner import aggregate_status, load_problem, run_test_cases
from services.judge0 import LANGUAGE_IDS

router = APIRouter(prefix="/api/interviews/{session_id}/code", tags=["code"])


def _require_session_owner(session_id: str, clerk_user_id: str) -> dict:
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return doc


def _validate_request(session_id: str, body: CodeRunRequest, clerk_user_id: str) -> tuple[dict, dict]:
    _require_session_owner(session_id, clerk_user_id)

    if body.language not in LANGUAGE_IDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported language '{body.language}'. Supported: {list(LANGUAGE_IDS.keys())}",
        )

    if not ObjectId.is_valid(body.question_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid question id")

    question = db.questions.find_one({
        "_id": ObjectId(body.question_id),
        "session_id": session_id,
    })
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    problem_id = question.get("coding_problem_id")
    if not problem_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No coding problem attached to this question")

    problem = load_problem(problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Problem '{problem_id}' not found")

    return question, problem


def _build_response(raw_results: list[dict], submission_id: str | None) -> CodeRunResponse:
    test_results = [
        TestResultResponse(
            test_case_id=r["test_case_id"],
            passed=r["passed"],
            stdout=r["stdout"],
            stderr=r["stderr"],
            runtime_ms=r["runtime_ms"],
        )
        for r in raw_results
    ]
    overall_status = aggregate_status([r["status"] for r in raw_results])
    passed = sum(1 for r in raw_results if r["passed"])
    return CodeRunResponse(
        passed_count=passed,
        total_count=len(raw_results),
        status=overall_status,
        test_results=test_results,
        submission_id=submission_id,
    )


@router.post("/run", response_model=CodeRunResponse)
async def run_code(
    session_id: str,
    body: CodeRunRequest,
    clerk_user_id: str = Depends(require_auth),
):
    _, problem = _validate_request(session_id, body, clerk_user_id)

    raw_results = await run_test_cases(
        source_code=body.code,
        language=body.language,
        problem=problem,
        include_hidden=False,
    )

    return _build_response(raw_results, submission_id=None)


@router.post("/submit", response_model=CodeRunResponse)
async def submit_code(
    session_id: str,
    body: CodeRunRequest,
    clerk_user_id: str = Depends(require_auth),
):
    _, problem = _validate_request(session_id, body, clerk_user_id)

    raw_results = await run_test_cases(
        source_code=body.code,
        language=body.language,
        problem=problem,
        include_hidden=True,
    )

    response = _build_response(raw_results, submission_id=None)

    test_result_docs = [
        TestResult(
            test_case_id=r["test_case_id"],
            passed=r["passed"],
            stdout=r["stdout"],
            stderr=r["stderr"],
            runtime_ms=r["runtime_ms"],
        )
        for r in raw_results
    ]
    submission = CodeSubmission(
        session_id=session_id,
        question_id=body.question_id,
        language=body.language,
        code=body.code,
        is_final=True,
        status=response.status,
        passed_count=response.passed_count,
        total_count=response.total_count,
        test_results=test_result_docs,
    )
    result = db.code_submissions.insert_one(submission.to_mongo())
    response.submission_id = str(result.inserted_id)

    return response
