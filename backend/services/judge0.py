import httpx
from fastapi import HTTPException, status
from config import settings
from models.code_submission import SubmissionStatus

LANGUAGE_IDS: dict[str, int] = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "cpp": 54,
    "go": 60,
}

_JUDGE0_STATUS_MAP: dict[int, SubmissionStatus] = {
    3: SubmissionStatus.accepted,
    4: SubmissionStatus.wrong_answer,
    5: SubmissionStatus.time_limit_exceeded,
    6: SubmissionStatus.compile_error,
}


def _map_status(status_id: int) -> SubmissionStatus:
    if status_id in _JUDGE0_STATUS_MAP:
        return _JUDGE0_STATUS_MAP[status_id]
    if status_id >= 7:
        return SubmissionStatus.runtime_error
    return SubmissionStatus.runtime_error


async def submit_to_judge0(
    source_code: str,
    language: str,
    stdin: str,
    expected_output: str,
) -> dict:
    """Submit one test case to Judge0 CE and return a result dict.

    Returns:
        {
            "status": SubmissionStatus,
            "passed": bool,
            "stdout": str,
            "stderr": str,
            "runtime_ms": float | None,
        }
    """
    language_id = LANGUAGE_IDS[language]
    payload = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin,
        "expected_output": expected_output,
    }
    headers = {
        "X-RapidAPI-Key": settings.judge0_api_key,
        "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
        "Content-Type": "application/json",
    }
    url = f"{settings.judge0_api_url}/submissions"
    params = {"base64_encoded": "false", "wait": "true"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers, params=params)
            resp.raise_for_status()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Code execution service unavailable",
            )

    data = resp.json()
    status_id = data.get("status", {}).get("id", 13)
    sub_status = _map_status(status_id)
    stdout = (data.get("stdout") or "").strip()
    stderr = (data.get("stderr") or "").strip()
    time_str = data.get("time")
    runtime_ms = float(time_str) * 1000 if time_str else None

    return {
        "status": sub_status,
        "passed": sub_status == SubmissionStatus.accepted,
        "stdout": stdout,
        "stderr": stderr,
        "runtime_ms": runtime_ms,
    }
