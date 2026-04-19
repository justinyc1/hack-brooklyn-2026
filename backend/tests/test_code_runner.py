import pytest
from unittest.mock import AsyncMock, patch
from models.code_submission import SubmissionStatus
from services.code_runner import aggregate_status, load_problem, run_test_cases


def test_aggregate_status_all_accepted():
    statuses = [SubmissionStatus.accepted, SubmissionStatus.accepted]
    assert aggregate_status(statuses) == SubmissionStatus.accepted


def test_aggregate_status_compile_error_wins():
    statuses = [SubmissionStatus.compile_error, SubmissionStatus.accepted]
    assert aggregate_status(statuses) == SubmissionStatus.compile_error


def test_aggregate_status_tle():
    statuses = [SubmissionStatus.accepted, SubmissionStatus.time_limit_exceeded]
    assert aggregate_status(statuses) == SubmissionStatus.time_limit_exceeded


def test_aggregate_status_runtime_error():
    statuses = [SubmissionStatus.accepted, SubmissionStatus.runtime_error]
    assert aggregate_status(statuses) == SubmissionStatus.runtime_error


def test_aggregate_status_wrong_answer():
    statuses = [SubmissionStatus.accepted, SubmissionStatus.wrong_answer]
    assert aggregate_status(statuses) == SubmissionStatus.wrong_answer


def test_load_problem_found():
    problem = load_problem("two-sum")
    assert problem["id"] == "two-sum"
    assert len(problem["test_cases"]) > 0


def test_load_problem_not_found():
    assert load_problem("nonexistent-problem") is None


@pytest.mark.asyncio
async def test_run_test_cases_public_only():
    problem = load_problem("two-sum")
    public_cases = [tc for tc in problem["test_cases"] if not tc["is_hidden"]]

    fake_result = {
        "status": SubmissionStatus.accepted,
        "passed": True,
        "stdout": "[0,1]",
        "stderr": "",
        "runtime_ms": 10.0,
    }

    with patch("services.code_runner.submit_to_judge0", new=AsyncMock(return_value=fake_result)):
        results = await run_test_cases(
            source_code="...",
            language="python",
            problem=problem,
            include_hidden=False,
        )

    assert len(results) == len(public_cases)
    assert all(r["passed"] for r in results)


@pytest.mark.asyncio
async def test_run_test_cases_all_cases():
    problem = load_problem("two-sum")
    total_cases = problem["test_cases"]

    fake_result = {
        "status": SubmissionStatus.accepted,
        "passed": True,
        "stdout": "[0,1]",
        "stderr": "",
        "runtime_ms": 10.0,
    }

    with patch("services.code_runner.submit_to_judge0", new=AsyncMock(return_value=fake_result)):
        results = await run_test_cases(
            source_code="...",
            language="python",
            problem=problem,
            include_hidden=True,
        )

    assert len(results) == len(total_cases)


@pytest.mark.asyncio
async def test_run_test_cases_short_circuits_on_compile_error():
    problem = load_problem("two-sum")

    fake_compile_error = {
        "status": SubmissionStatus.compile_error,
        "passed": False,
        "stdout": "",
        "stderr": "SyntaxError",
        "runtime_ms": None,
    }

    with patch("services.code_runner.submit_to_judge0", new=AsyncMock(return_value=fake_compile_error)):
        results = await run_test_cases(
            source_code="def bad(:",
            language="python",
            problem=problem,
            include_hidden=True,
        )

    assert len(results) == 1
    assert results[0]["status"] == SubmissionStatus.compile_error
