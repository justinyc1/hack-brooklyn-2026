import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from services.judge0 import submit_to_judge0, LANGUAGE_IDS
from models.code_submission import SubmissionStatus


def test_language_ids_map_has_all_five():
    for lang in ("python", "javascript", "java", "cpp", "go"):
        assert lang in LANGUAGE_IDS


@pytest.mark.asyncio
async def test_submit_accepted():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "status": {"id": 3, "description": "Accepted"},
        "stdout": "[0,1]\n",
        "stderr": None,
        "time": "0.05",
    }

    with patch("services.judge0.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await submit_to_judge0(
            source_code="print('[0,1]')",
            language="python",
            stdin="[2,7,11,15]\n9",
            expected_output="[0,1]",
        )

    assert result["status"] == SubmissionStatus.accepted
    assert result["passed"] is True
    assert result["stdout"] == "[0,1]"
    assert result["runtime_ms"] == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_submit_wrong_answer():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "status": {"id": 4, "description": "Wrong Answer"},
        "stdout": "[0,2]\n",
        "stderr": None,
        "time": "0.03",
    }

    with patch("services.judge0.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await submit_to_judge0(
            source_code="print('[0,2]')",
            language="python",
            stdin="[2,7,11,15]\n9",
            expected_output="[0,1]",
        )

    assert result["status"] == SubmissionStatus.wrong_answer
    assert result["passed"] is False


@pytest.mark.asyncio
async def test_submit_compile_error():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "status": {"id": 6, "description": "Compilation Error"},
        "stdout": None,
        "stderr": "SyntaxError: invalid syntax",
        "time": None,
    }

    with patch("services.judge0.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await submit_to_judge0(
            source_code="def bad(:",
            language="python",
            stdin="",
            expected_output="",
        )

    assert result["status"] == SubmissionStatus.compile_error
    assert result["passed"] is False
    assert "SyntaxError" in result["stderr"]


@pytest.mark.asyncio
async def test_submit_judge0_http_error_raises():
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = Exception("Service unavailable")

    with patch("services.judge0.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await submit_to_judge0(
                source_code="print(1)",
                language="python",
                stdin="",
                expected_output="",
            )
        assert exc_info.value.status_code == 502
        assert "Code execution service unavailable" in exc_info.value.detail
