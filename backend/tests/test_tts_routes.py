import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app

FAKE_AUDIO = b"fake-mp3-bytes"
FAKE_PRESIGNED = "https://s3.example.com/tts-cache/abc123.mp3?sig=xyz"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_presigned_url_returns_200_on_cache_hit(client):
    with patch("routes.tts.ensure_cached", new=AsyncMock(return_value=(FAKE_AUDIO, True, "tts-cache/abc.mp3"))), \
         patch("routes.tts.generate_presigned_url", return_value=FAKE_PRESIGNED):

        resp = client.get(
            "/api/tts/presigned-url",
            params={"text": "Hello!", "voice_id": "21m00Tcm4TlvDq8ikWAM"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == FAKE_PRESIGNED
    assert data["cached"] is True


def test_presigned_url_returns_200_on_cache_miss(client):
    with patch("routes.tts.ensure_cached", new=AsyncMock(return_value=(FAKE_AUDIO, False, "tts-cache/abc.mp3"))), \
         patch("routes.tts.generate_presigned_url", return_value=FAKE_PRESIGNED):

        resp = client.get(
            "/api/tts/presigned-url",
            params={"text": "Let's begin.", "voice_id": "21m00Tcm4TlvDq8ikWAM"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["cached"] is False


def test_presigned_url_requires_text_and_voice_id(client):
    resp = client.get("/api/tts/presigned-url", params={"text": "Hello!"})
    assert resp.status_code == 422


def test_presigned_url_validates_stability_range(client):
    resp = client.get(
        "/api/tts/presigned-url",
        params={"text": "Hi", "voice_id": "abc", "stability": 1.5},
    )
    assert resp.status_code == 422
