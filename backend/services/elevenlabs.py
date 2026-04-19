"""ElevenLabs Conversational AI integration.

Flow per interview session:
  1. create_interview_agent()  — one agent per session, returns agent_id
  2. get_signed_url()          — returns a short-lived wss:// URL the frontend uses
  3. sync_transcript()         — called on session completion; pulls ElevenLabs
                                 conversation transcript and persists to MongoDB
"""

from datetime import datetime, timedelta, timezone

import httpx
from bson import ObjectId

from config import settings
from db import db
from models.transcript import Speaker, TranscriptSegment

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

_TONE_PERSONA = {
    "friendly": (
        "You are a warm, encouraging interviewer. Be supportive and put the candidate at ease, "
        "but still probe for depth and specifics when answers are vague."
    ),
    "neutral": (
        "You are a professional, balanced interviewer. Maintain a calm, objective tone. "
        "Ask follow-up questions when answers lack detail or structure."
    ),
    "intense": (
        "You are a demanding, fast-paced interviewer. Keep the pressure on — ask sharp follow-ups, "
        "push back on weak answers, and hold the candidate to a high bar."
    ),
    "skeptical": (
        "You are a skeptical, probing interviewer. Question assumptions, challenge claims, "
        "and dig for evidence. Don't accept surface-level answers."
    ),
}


def _build_system_prompt(session, questions: list) -> str:
    persona = _TONE_PERSONA.get(session.interviewer_tone.value, _TONE_PERSONA["neutral"])
    mode = session.mode.value
    company_str = f" at {session.company}" if session.company else ""
    duration = session.duration_minutes

    question_list = "\n".join(
        f"{i + 1}. [{q.type.value.upper()}] {q.prompt}" for i, q in enumerate(questions)
    )

    return f"""{persona}

You are conducting a {mode} mock interview for a {session.role} position{company_str}. \
The interview lasts approximately {duration} minutes.

Interview plan — ask these questions in order, then follow up naturally based on the candidate's responses:
{question_list}

Conduct guidelines:
- Open with a brief professional greeting and a one-sentence description of the format.
- Ask one question at a time and wait for a complete response before moving on.
- If an answer is vague, incomplete, or lacks a concrete example, ask a targeted follow-up.
- Do not skip questions unless time is clearly running out.
- Close the interview professionally once all questions are covered or time is nearly up.
- Stay in character throughout — do not break the fourth wall or mention that you are an AI."""


async def create_interview_agent(session, questions: list) -> str:
    """Create a per-session ElevenLabs conversational agent. Returns agent_id."""
    company_str = f" at {session.company}" if session.company else ""
    first_message = (
        f"Hello! Thank you for joining today. I'll be your interviewer for the "
        f"{session.role} position{company_str}. We have about {session.duration_minutes} minutes. "
        f"Let's get started — could you begin by briefly introducing yourself?"
    )

    payload = {
        "name": f"Interviewer-{session.id}",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": _build_system_prompt(session, questions),
                    "llm": "gemini-2.0-flash-001",
                    "temperature": 0.6,
                },
                "first_message": first_message,
                "language": "en",
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
                "optimize_streaming_latency": 3,
                "stability": 0.5,
                "similarity_boost": 0.8,
            },
            "asr": {"quality": "high"},
            "turn": {"turn_timeout": 8},
        },
        "platform_settings": {
            "max_duration_seconds": session.duration_minutes * 60 + 60,
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{ELEVENLABS_BASE}/convai/agents/create",
            headers={"xi-api-key": settings.elevenlabs_api_key},
            json=payload,
        )
        if not resp.is_success:
            raise RuntimeError(f"ElevenLabs agent creation failed {resp.status_code}: {resp.text}")
        return resp.json()["agent_id"]


async def get_signed_url(agent_id: str) -> str:
    """Return a short-lived signed WebSocket URL for the frontend to connect to."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{ELEVENLABS_BASE}/convai/conversation/get_signed_url",
            headers={"xi-api-key": settings.elevenlabs_api_key},
            params={"agent_id": agent_id},
        )
        resp.raise_for_status()
        return resp.json()["signed_url"]


async def sync_transcript(session_id: str, conversation_id: str, started_at: datetime | None = None) -> int:
    """Fetch the ElevenLabs conversation transcript and upsert into MongoDB.

    Returns the number of segments written.
    """
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{ELEVENLABS_BASE}/convai/conversations/{conversation_id}",
            headers={"xi-api-key": settings.elevenlabs_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    raw_segments: list[dict] = data.get("transcript", [])
    if not raw_segments:
        return 0

    base_time = started_at or datetime.now(timezone.utc)

    # Replace any previously synced segments to avoid duplicates on retry
    db.transcripts.delete_many({"session_id": session_id, "is_partial": False})

    docs = []
    for seg in raw_segments:
        role = seg.get("role", "user")
        speaker = Speaker.interviewer if role == "agent" else Speaker.user
        offset_secs = seg.get("time_in_call_secs", 0.0)
        timestamp = base_time + timedelta(seconds=offset_secs)

        segment = TranscriptSegment(
            session_id=session_id,
            speaker=speaker,
            text=seg.get("message", "").strip(),
            is_partial=False,
            timestamp=timestamp,
        )
        docs.append(segment.to_mongo())

    if docs:
        db.transcripts.insert_many(docs)

    return len(docs)
