from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from auth.clerk import require_auth

FAKE_USER_ID = "user_test123"
FAKE_SESSION_ID = "507f1f77bcf86cd799439011"
FAKE_PRESIGNED = "https://s3.example.com/reports/abc/feedback.html?sig=xyz"

FAKE_FEEDBACK_DOC = {
    "_id": "507f1f77bcf86cd799439012",
    "session_id": FAKE_SESSION_ID,
    "overall_score": 7.5,
    "category_scores": {"clarity": 8.0, "confidence": 7.0},
    "per_question_feedback": [],
    "top_strengths": ["Good clarity"],
    "top_weaknesses": ["Needs improvement"],
    "targeted_drills": [],
    "generated_at": "2026-04-25T12:00:00Z",
    "report_s3_key": None,
}

FAKE_SESSION_DOC = {
    "_id": FAKE_SESSION_ID,
    "clerk_user_id": FAKE_USER_ID,
    "mode": "technical",
    "role": "Software Engineer",
    "company": "Acme",
    "difficulty": "medium",
    "duration_minutes": 45,
    "interviewer_tone": "neutral",
    "behavioral_persona": None,
    "status": "completed",
    "question_ids": [],
    "elevenlabs_agent_id": None,
    "elevenlabs_conversation_id": None,
    "audio_s3_url": None,
    "created_at": "2026-04-25T00:00:00Z",
    "started_at": None,
    "ended_at": None,
}


def override_auth():
    return FAKE_USER_ID


def test_share_creates_s3_object_and_returns_url():
    mock_db = MagicMock()
    mock_db.sessions.find_one.return_value = FAKE_SESSION_DOC
    mock_db.feedback.find_one.return_value = {**FAKE_FEEDBACK_DOC, "report_s3_key": None}
    mock_db.feedback.update_one.return_value = MagicMock()

    mock_s3 = MagicMock()
    mock_s3.put_object.return_value = {}

    with (
        patch("routes.feedback.db", mock_db),
        patch("routes.feedback.s3_client", mock_s3),
        patch("routes.feedback.generate_presigned_url", return_value=FAKE_PRESIGNED),
    ):
        app.dependency_overrides[require_auth] = override_auth
        client = TestClient(app)
        resp = client.post(f"/api/feedback/{FAKE_SESSION_ID}/share")
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == FAKE_PRESIGNED
    assert data["expires_in"] == 604800
    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args.kwargs
    assert call_kwargs["ContentType"] == "text/html; charset=utf-8"
    assert b"<!DOCTYPE html>" in call_kwargs["Body"]


def test_share_reuses_existing_s3_key_without_re_uploading():
    existing_key = f"reports/{FAKE_SESSION_ID}/feedback.html"
    mock_db = MagicMock()
    mock_db.sessions.find_one.return_value = FAKE_SESSION_DOC
    mock_db.feedback.find_one.return_value = {**FAKE_FEEDBACK_DOC, "report_s3_key": existing_key}

    mock_s3 = MagicMock()

    with (
        patch("routes.feedback.db", mock_db),
        patch("routes.feedback.s3_client", mock_s3),
        patch("routes.feedback.generate_presigned_url", return_value=FAKE_PRESIGNED),
    ):
        app.dependency_overrides[require_auth] = override_auth
        client = TestClient(app)
        resp = client.post(f"/api/feedback/{FAKE_SESSION_ID}/share")
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["url"] == FAKE_PRESIGNED
    mock_s3.put_object.assert_not_called()


def test_share_returns_404_when_no_feedback():
    mock_db = MagicMock()
    mock_db.sessions.find_one.return_value = FAKE_SESSION_DOC
    mock_db.feedback.find_one.return_value = None

    with patch("routes.feedback.db", mock_db):
        app.dependency_overrides[require_auth] = override_auth
        client = TestClient(app)
        resp = client.post(f"/api/feedback/{FAKE_SESSION_ID}/share")
        app.dependency_overrides.clear()

    assert resp.status_code == 404


def test_share_returns_404_for_wrong_owner():
    mock_db = MagicMock()
    # sessions.find_one returns None → _require_session_owner raises 404
    mock_db.sessions.find_one.return_value = None

    with patch("routes.feedback.db", mock_db):
        app.dependency_overrides[require_auth] = override_auth
        client = TestClient(app)
        resp = client.post(f"/api/feedback/{FAKE_SESSION_ID}/share")
        app.dependency_overrides.clear()

    assert resp.status_code == 404


def test_share_returns_400_for_invalid_session_id():
    with patch("routes.feedback.db", MagicMock()):
        app.dependency_overrides[require_auth] = override_auth
        client = TestClient(app)
        resp = client.post("/api/feedback/not-a-valid-id/share")
        app.dependency_overrides.clear()

    assert resp.status_code == 400
