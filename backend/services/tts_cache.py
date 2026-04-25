import hashlib
import logging

import httpx
from botocore.exceptions import ClientError

from config import settings
from services.s3 import BUCKET_NAME, s3_client

logger = logging.getLogger(__name__)

_ELEVENLABS_TTS_BASE = "https://api.elevenlabs.io/v1/text-to-speech"


def _cache_key(text: str, voice_id: str, stability: float, similarity_boost: float) -> str:
    raw = f"{voice_id}|{stability:.4f}|{similarity_boost:.4f}|{text}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _s3_key(cache_key: str) -> str:
    return f"tts-cache/{cache_key}.mp3"


async def ensure_cached(
    text: str,
    voice_id: str,
    stability: float,
    similarity_boost: float,
) -> tuple[bytes, bool, str]:
    """Return (audio_bytes, was_cached, s3_key). Fetches from S3 or calls ElevenLabs TTS API."""
    key = _cache_key(text, voice_id, stability, similarity_boost)
    s3_obj_key = _s3_key(key)

    try:
        resp = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_obj_key)
        return resp["Body"].read(), True, s3_obj_key
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code not in ("NoSuchKey", "NoSuchObject"):
            logger.warning("S3 cache read error (%s) for %s: %s", code, s3_obj_key, exc)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_ELEVENLABS_TTS_BASE}/{voice_id}",
            headers={"xi-api-key": settings.elevenlabs_api_key},
            json={
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                },
            },
        )
        resp.raise_for_status()
        audio = resp.content

    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_obj_key,
            Body=audio,
            ContentType="audio/mpeg",
        )
    except Exception as exc:
        logger.error("Failed to write TTS cache to S3 (%s): %s", s3_obj_key, exc)

    return audio, False, s3_obj_key


def _s3_key_for(text: str, voice_id: str, stability: float, similarity_boost: float) -> str:
    return _s3_key(_cache_key(text, voice_id, stability, similarity_boost))


async def prewarm(
    text: str,
    voice_id: str,
    stability: float,
    similarity_boost: float,
) -> None:
    """Pre-synthesize and cache audio. Silently ignores all errors (fire-and-forget)."""
    try:
        await ensure_cached(text, voice_id, stability, similarity_boost)
    except Exception as exc:
        logger.warning("TTS prewarm failed for voice %s: %s", voice_id, exc)
