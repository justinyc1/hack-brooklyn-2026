import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from auth.clerk import require_auth
from db import db
from models.code_submission import CodeSubmission, SubmissionStatus, TestResult
from schemas.code import CodeRunRequest, CodeRunResponse, TestResultResponse
from schemas.interviews import CodeSnapshotRequest, CodeSnapshotDetail
from services.code_runner import aggregate_status, load_problem, run_test_cases
from services.judge0 import LANGUAGE_IDS
from services.s3 import get_s3_key_for_artifact, upload_json_to_s3, download_json_from_s3

logger = logging.getLogger(__name__)

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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    if not problem.get("test_cases"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Problem '{problem_id}' has no test cases")

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


from auth.rate_limit import RateLimiter

@router.post("/run", response_model=CodeRunResponse)
async def run_code(
    session_id: str,
    body: CodeRunRequest,
    clerk_user_id: str = Depends(RateLimiter(15, 60, "code_run")),
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
    clerk_user_id: str = Depends(RateLimiter(10, 60, "code_submit")),
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


@router.post("/snapshot", status_code=204)
def save_code_snapshot(
    session_id: str,
    body: CodeSnapshotRequest,
    clerk_user_id: str = Depends(require_auth),
):
    doc = _require_session_owner(session_id, clerk_user_id)
    if doc.get("status") != "active":
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    s3_key = get_s3_key_for_artifact(
        session_id, "code_snapshots", f"snapshot_{body.sequence:04d}.json"
    )
    snapshot_data = {
        "sequence": body.sequence,
        "language": body.language,
        "code": body.code,
        "timestamp": timestamp,
    }

    try:
        upload_json_to_s3(snapshot_data, s3_key)
    except Exception as exc:
        logger.error("Snapshot upload failed for session %s: %s", session_id, exc)
        return

    db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$push": {"code_snapshots": {
            "s3_key": s3_key,
            "sequence": body.sequence,
            "language": body.language,
            "timestamp": timestamp,
        }}},
    )


@router.get("/snapshots", response_model=list[CodeSnapshotDetail])
def get_code_snapshots(
    session_id: str,
    clerk_user_id: str = Depends(require_auth),
):
    doc = _require_session_owner(session_id, clerk_user_id)
    meta_list = doc.get("code_snapshots", [])

    result = []
    for meta in meta_list:
        data = download_json_from_s3(meta["s3_key"])
        if data:
            result.append(CodeSnapshotDetail(
                sequence=meta["sequence"],
                language=meta["language"],
                timestamp=meta["timestamp"],
                code=data["code"],
            ))

    return sorted(result, key=lambda x: x.sequence)
