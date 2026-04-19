import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch


TAVILY_RESPONSE = {
    "results": [
        {"title": "Google SWE Interview", "content": "Google focuses on system design and algorithms. Behavioral questions use STAR format. Culture fit is important."},
        {"title": "Google Leetcode", "content": "Google commonly asks dynamic programming, graphs, and tree traversal problems."},
    ]
}

LLM_SYNTHESIS_RESPONSE = json.dumps({
    "behavioral_themes": [
        {"theme": "Leadership and ownership", "confidence": 0.9},
        {"theme": "Dealing with ambiguity", "confidence": 0.8},
    ],
    "technical_focus": [
        {"theme": "Dynamic programming", "confidence": 0.85},
        {"theme": "System design", "confidence": 0.9},
    ],
    "style_signals": [
        {"theme": "STAR format expected", "confidence": 0.95},
        {"theme": "Collaborative culture emphasis", "confidence": 0.75},
    ],
})


@pytest.mark.asyncio
async def test_fetch_snapshot_returns_structured_data():
    from services.company_research import fetch_snapshot

    with patch("services.company_research._tavily_search", new=AsyncMock(return_value=TAVILY_RESPONSE["results"])), \
         patch("services.company_research.chat_complete", new=AsyncMock(return_value=LLM_SYNTHESIS_RESPONSE)):
        result = await fetch_snapshot("Google", "Software Engineer")

    assert result["company"] == "Google"
    assert result["role"] == "Software Engineer"
    assert len(result["behavioral_themes"]) == 2
    assert result["behavioral_themes"][0]["theme"] == "Leadership and ownership"
    assert result["behavioral_themes"][0]["confidence"] == pytest.approx(0.9)
    assert len(result["technical_focus"]) == 2
    assert len(result["style_signals"]) == 2


@pytest.mark.asyncio
async def test_fetch_snapshot_falls_back_on_tavily_failure():
    from services.company_research import fetch_snapshot

    with patch("services.company_research._tavily_search", new=AsyncMock(side_effect=Exception("Tavily down"))):
        result = await fetch_snapshot("Google", "Software Engineer")

    assert result["company"] == "Google"
    assert result["behavioral_themes"] == []
    assert result["technical_focus"] == []
    assert result["style_signals"] == []


@pytest.mark.asyncio
async def test_fetch_snapshot_falls_back_on_llm_failure():
    from services.company_research import fetch_snapshot

    with patch("services.company_research._tavily_search", new=AsyncMock(return_value=TAVILY_RESPONSE["results"])), \
         patch("services.company_research.chat_complete", new=AsyncMock(side_effect=Exception("LLM down"))):
        result = await fetch_snapshot("Google", "Software Engineer")

    assert result["company"] == "Google"
    assert result["behavioral_themes"] == []
    assert result["technical_focus"] == []
    assert result["style_signals"] == []


def test_is_fresh_returns_true_within_ttl():
    from services.company_research import _is_fresh

    recent = datetime.now(timezone.utc) - timedelta(days=3)
    assert _is_fresh(recent) is True


def test_is_fresh_returns_false_outside_ttl():
    from services.company_research import _is_fresh

    old = datetime.now(timezone.utc) - timedelta(days=8)
    assert _is_fresh(old) is False


@pytest.mark.asyncio
async def test_get_or_fetch_returns_cached_when_fresh(monkeypatch):
    from services.company_research import get_or_fetch_snapshot

    fresh_doc = {
        "_id": "abc123",
        "company": "Google",
        "role": "Software Engineer",
        "behavioral_themes": [{"theme": "Leadership", "confidence": 0.9}],
        "technical_focus": [],
        "style_signals": [],
        "retrieved_at": datetime.now(timezone.utc) - timedelta(days=1),
    }

    mock_db = MagicMock()
    mock_db.company_snapshots.find_one.return_value = fresh_doc
    monkeypatch.setattr("services.company_research.db", mock_db)

    result = await get_or_fetch_snapshot("Google", "Software Engineer")

    mock_db.company_snapshots.find_one.assert_called_once()
    assert result["company"] == "Google"
    assert result["behavioral_themes"][0]["theme"] == "Leadership"


@pytest.mark.asyncio
async def test_get_or_fetch_returns_cached_when_fresh_does_not_call_tavily(monkeypatch):
    from services.company_research import get_or_fetch_snapshot

    fresh_doc = {
        "_id": "abc123",
        "company": "Google",
        "role": "Software Engineer",
        "behavioral_themes": [],
        "technical_focus": [],
        "style_signals": [],
        "retrieved_at": datetime.now(timezone.utc) - timedelta(days=1),
    }

    mock_db = MagicMock()
    mock_db.company_snapshots.find_one.return_value = fresh_doc
    monkeypatch.setattr("services.company_research.db", mock_db)

    fetch_mock = AsyncMock()
    monkeypatch.setattr("services.company_research.fetch_snapshot", fetch_mock)

    await get_or_fetch_snapshot("Google", "Software Engineer")

    fetch_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_fetch_refetches_stale_cache(monkeypatch):
    from services.company_research import get_or_fetch_snapshot

    stale_doc = {
        "_id": "abc123",
        "company": "Google",
        "role": "Software Engineer",
        "behavioral_themes": [],
        "technical_focus": [],
        "style_signals": [],
        "retrieved_at": datetime.now(timezone.utc) - timedelta(days=10),
    }
    fresh_data = {
        "company": "Google",
        "role": "Software Engineer",
        "behavioral_themes": [{"theme": "Leadership", "confidence": 0.9}],
        "technical_focus": [],
        "style_signals": [],
    }

    mock_db = MagicMock()
    mock_db.company_snapshots.find_one.return_value = stale_doc
    monkeypatch.setattr("services.company_research.db", mock_db)

    fetch_mock = AsyncMock(return_value=fresh_data)
    monkeypatch.setattr("services.company_research.fetch_snapshot", fetch_mock)

    result = await get_or_fetch_snapshot("Google", "Software Engineer")

    fetch_mock.assert_called_once_with("Google", "Software Engineer")
    assert result["behavioral_themes"][0]["theme"] == "Leadership"


@pytest.mark.asyncio
async def test_get_or_fetch_fetches_when_no_cache(monkeypatch):
    from services.company_research import get_or_fetch_snapshot

    fresh_data = {
        "company": "Meta",
        "role": None,
        "behavioral_themes": [],
        "technical_focus": [{"theme": "Distributed systems", "confidence": 0.8}],
        "style_signals": [],
    }

    mock_db = MagicMock()
    mock_db.company_snapshots.find_one.return_value = None
    monkeypatch.setattr("services.company_research.db", mock_db)

    fetch_mock = AsyncMock(return_value=fresh_data)
    monkeypatch.setattr("services.company_research.fetch_snapshot", fetch_mock)

    result = await get_or_fetch_snapshot("Meta", None)

    fetch_mock.assert_called_once_with("Meta", None)
    mock_db.company_snapshots.replace_one.assert_called_once()
    assert result["technical_focus"][0]["theme"] == "Distributed systems"


# --- Route schema test ---

def test_get_snapshot_schema_fields():
    """Verify schema fields match what the service returns."""
    from schemas.companies import CompanySnapshotResponse, ThemeScoreResponse

    resp = CompanySnapshotResponse(
        company="Google",
        role="Software Engineer",
        behavioral_themes=[ThemeScoreResponse(theme="Leadership", confidence=0.9)],
        technical_focus=[],
        style_signals=[],
        retrieved_at=datetime.now(timezone.utc),
        is_fresh=True,
    )
    assert resp.company == "Google"
    assert resp.behavioral_themes[0].confidence == pytest.approx(0.9)
    assert resp.is_fresh is True


# --- _doc_to_response tests ---

def test_doc_to_response_coerces_naive_datetime():
    from routes.companies import _doc_to_response

    naive_dt = datetime(2026, 1, 1, 12, 0, 0)  # no tzinfo
    doc = {
        "company": "Google",
        "role": "SWE",
        "behavioral_themes": [],
        "technical_focus": [],
        "style_signals": [],
        "retrieved_at": naive_dt,
    }
    resp = _doc_to_response(doc)
    assert resp.retrieved_at.tzinfo is not None


def test_doc_to_response_fresh_sets_is_fresh_true():
    from routes.companies import _doc_to_response

    recent_dt = datetime.now(timezone.utc) - timedelta(days=1)
    doc = {
        "company": "Meta",
        "role": None,
        "behavioral_themes": [{"theme": "Speed", "confidence": 0.8}],
        "technical_focus": [],
        "style_signals": [],
        "retrieved_at": recent_dt,
    }
    resp = _doc_to_response(doc)
    assert resp.is_fresh is True
    assert resp.behavioral_themes[0].theme == "Speed"


def test_doc_to_response_stale_sets_is_fresh_false():
    from routes.companies import _doc_to_response

    old_dt = datetime.now(timezone.utc) - timedelta(days=10)
    doc = {
        "company": "Amazon",
        "role": "SDE",
        "behavioral_themes": [],
        "technical_focus": [],
        "style_signals": [],
        "retrieved_at": old_dt,
    }
    resp = _doc_to_response(doc)
    assert resp.is_fresh is False


def test_doc_to_response_missing_retrieved_at_uses_now():
    from routes.companies import _doc_to_response

    doc = {
        "company": "Apple",
        "role": None,
        "behavioral_themes": [],
        "technical_focus": [],
        "style_signals": [],
    }
    resp = _doc_to_response(doc)
    assert resp.retrieved_at is not None
    assert resp.is_fresh is True
