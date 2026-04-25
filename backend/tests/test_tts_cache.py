import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from botocore.exceptions import ClientError


# ── helpers ────────────────────────────────────────────────────────────────

FAKE_AUDIO = b"fake-mp3-bytes"
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
STABILITY = 0.65
SIMILARITY = 0.80
TEXT = "Hello! Let's begin."


def _client_error():
    return ClientError({"Error": {"Code": "NoSuchKey", "Message": ""}}, "GetObject")


# ── tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_miss_calls_elevenlabs_and_stores():
    """On cache miss: calls ElevenLabs TTS, puts result in S3."""
    mock_s3 = MagicMock()
    mock_s3.get_object.side_effect = _client_error()
    mock_s3.put_object.return_value = {}

    mock_resp = MagicMock()
    mock_resp.content = FAKE_AUDIO
    mock_resp.raise_for_status = MagicMock()

    with patch("services.tts_cache.s3_client", mock_s3), \
         patch("services.tts_cache.settings") as mock_cfg, \
         patch("httpx.AsyncClient") as mock_httpx_cls:
        mock_cfg.elevenlabs_api_key = "test-key"
        mock_httpx = AsyncMock()
        mock_httpx.post.return_value = mock_resp
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_httpx)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from services import tts_cache
        audio, cached, s3_key = await tts_cache.ensure_cached(TEXT, VOICE_ID, STABILITY, SIMILARITY)

    assert audio == FAKE_AUDIO
    assert cached is False
    assert s3_key.startswith("tts-cache/") and s3_key.endswith(".mp3")
    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args.kwargs
    assert call_kwargs["ContentType"] == "audio/mpeg"
    assert call_kwargs["Body"] == FAKE_AUDIO


@pytest.mark.asyncio
async def test_cache_hit_returns_s3_bytes_without_calling_elevenlabs():
    """On cache hit: returns S3 bytes, skips ElevenLabs entirely."""
    mock_s3 = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = FAKE_AUDIO
    mock_s3.get_object.return_value = {"Body": mock_body}

    with patch("services.tts_cache.s3_client", mock_s3), \
         patch("httpx.AsyncClient") as mock_httpx_cls:

        from services import tts_cache
        audio, cached, s3_key = await tts_cache.ensure_cached(TEXT, VOICE_ID, STABILITY, SIMILARITY)

    assert audio == FAKE_AUDIO
    assert cached is True
    mock_httpx_cls.assert_not_called()


@pytest.mark.asyncio
async def test_prewarm_skips_when_key_already_exists():
    """prewarm does not call ElevenLabs when the S3 key already exists."""
    mock_s3 = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = FAKE_AUDIO
    mock_s3.get_object.return_value = {"Body": mock_body}

    with patch("services.tts_cache.s3_client", mock_s3), \
         patch("httpx.AsyncClient") as mock_httpx_cls:
        from services import tts_cache
        await tts_cache.prewarm(TEXT, VOICE_ID, STABILITY, SIMILARITY)

    mock_httpx_cls.assert_not_called()


@pytest.mark.asyncio
async def test_prewarm_silently_ignores_errors():
    """prewarm does not raise even when ElevenLabs call fails."""
    mock_s3 = MagicMock()
    mock_s3.get_object.side_effect = _client_error()
    mock_s3.put_object.return_value = {}

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("ElevenLabs down")

    with patch("services.tts_cache.s3_client", mock_s3), \
         patch("services.tts_cache.settings") as mock_cfg, \
         patch("httpx.AsyncClient") as mock_httpx_cls:
        mock_cfg.elevenlabs_api_key = "test-key"
        mock_httpx = AsyncMock()
        mock_httpx.post.return_value = mock_resp
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_httpx)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from services import tts_cache
        await tts_cache.prewarm(TEXT, VOICE_ID, STABILITY, SIMILARITY)  # must not raise


def test_s3_key_for_matches_ensure_cached_storage_key():
    from services.tts_cache import _s3_key_for, _cache_key, _s3_key
    key = _s3_key_for(TEXT, VOICE_ID, STABILITY, SIMILARITY)
    assert key == _s3_key(_cache_key(TEXT, VOICE_ID, STABILITY, SIMILARITY))
    assert key.startswith("tts-cache/")
    assert key.endswith(".mp3")
