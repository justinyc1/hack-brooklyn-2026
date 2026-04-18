import json
from pathlib import Path
from models.code_submission import SubmissionStatus
from services.judge0 import submit_to_judge0

_PROBLEMS_PATH = Path(__file__).parent.parent / "problems" / "problems.json"
_problems_cache: dict[str, dict] | None = None


def _load_all_problems() -> dict[str, dict]:
    global _problems_cache
    if _problems_cache is None:
        with open(_PROBLEMS_PATH) as f:
            problems_list = json.load(f)
        _problems_cache = {p["id"]: p for p in problems_list}
    return _problems_cache


def load_problem(problem_id: str) -> dict | None:
    return _load_all_problems().get(problem_id)


def aggregate_status(statuses: list[SubmissionStatus]) -> SubmissionStatus:
    if SubmissionStatus.compile_error in statuses:
        return SubmissionStatus.compile_error
    if all(s == SubmissionStatus.accepted for s in statuses):
        return SubmissionStatus.accepted
    if SubmissionStatus.time_limit_exceeded in statuses:
        return SubmissionStatus.time_limit_exceeded
    if SubmissionStatus.runtime_error in statuses:
        return SubmissionStatus.runtime_error
    return SubmissionStatus.wrong_answer


async def run_test_cases(
    source_code: str,
    language: str,
    problem: dict,
    include_hidden: bool,
) -> list[dict]:
    """Run test cases against Judge0 and return per-case result dicts."""
    cases = problem["test_cases"]
    if not include_hidden:
        cases = [tc for tc in cases if not tc["is_hidden"]]

    results = []
    for tc in cases:
        result = await submit_to_judge0(
            source_code=source_code,
            language=language,
            stdin=tc["stdin"],
            expected_output=tc["expected_stdout"],
        )
        results.append({
            "test_case_id": tc["id"],
            "passed": result["passed"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "runtime_ms": result["runtime_ms"],
            "status": result["status"],
        })

        if result["status"] == SubmissionStatus.compile_error:
            break

    return results
