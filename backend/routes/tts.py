import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.s3 import generate_presigned_url
from services.tts_cache import ensure_cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSPresignedUrlResponse(BaseModel):
    url: str
    cached: bool


@router.get("/presigned-url", response_model=TTSPresignedUrlResponse)
async def get_tts_presigned_url(
    text: str = Query(..., min_length=1),
    voice_id: str = Query(..., min_length=1),
    stability: float = Query(0.5, ge=0.0, le=1.0),
    similarity_boost: float = Query(0.8, ge=0.0, le=1.0),
):
    """Return a presigned S3 URL for TTS audio. Synthesizes and caches on first request."""
    try:
        _, cached, s3_key = await ensure_cached(text, voice_id, stability, similarity_boost)
    except Exception as exc:
        logger.error("TTS synthesis failed: %s", exc)
        raise HTTPException(status_code=502, detail="TTS synthesis failed")

    url = generate_presigned_url(s3_key, expiration=3600)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    return TTSPresignedUrlResponse(url=url, cached=cached)
