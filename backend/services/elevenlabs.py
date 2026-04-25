"""ElevenLabs Conversational AI integration.


Flow per interview session:
  1. create_interview_agent()  — one agent per session, returns (agent_id, first_message, voice_cfg)
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


# voice_id: ElevenLabs pre-made voice IDs
# stability: 0=expressive/varied, 1=consistent/monotone
# similarity_boost: faithfulness to the original voice character
_TONE_VOICE = {
    "friendly": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel — calm, warm American female
        "stability": 0.65,
        "similarity_boost": 0.80,
    },
    "neutral": {
        "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George — articulate, measured British male
        "stability": 0.70,
        "similarity_boost": 0.75,
    },
    "intense": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam — deep, commanding American male
        "stability": 0.38,
        "similarity_boost": 0.92,
    },
    "skeptical": {
        "voice_id": "N2lVS1w4EtoT3dr4eOWO",  # Callum — edgy, skeptical British male
        "stability": 0.52,
        "similarity_boost": 0.85,
    },
}

_BEHAVIORAL_VOICE = {
    "supportive": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah — gentle, warm female
        "stability": 0.65,
        "similarity_boost": 0.80,
    },
    "corporate": {
        "voice_id": "onwK4e9ZLuTAKqWW03F9",  # Daniel — authoritative British male
        "stability": 0.75,
        "similarity_boost": 0.75,
    },
    "pressure": {
        "voice_id": "D38z5RcWu1voky8WS1ja",  # Fin — confident, fast Irish male
        "stability": 0.32,
        "similarity_boost": 0.92,
    },
    "probing": {
        "voice_id": "2EiwWnXFnvU5JabPnv8n",  # Clyde — mature, scrutinizing American male
        "stability": 0.50,
        "similarity_boost": 0.87,
    },
}

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


_BEHAVIORAL_PERSONA = {
    "supportive": (
        "You are a warm, encouraging interviewer. Create a safe space for storytelling. "
        "Prompt the candidate to go deeper on impact, emotions, and personal growth. "
        "Celebrate specifics and gently guide vague answers toward concrete examples."
    ),
    "corporate": (
        "You are a formal, professional interviewer. Strictly enforce the STAR format — "
        "Situation, Task, Action, Result. If any component is missing, ask directly for it. "
        "Keep a measured, neutral tone throughout."
    ),
    "pressure": (
        "You are a fast-paced, no-nonsense interviewer. Cut off rambling answers politely "
        "but firmly. Demand conciseness — if an answer exceeds 90 seconds, interrupt and "
        "ask the candidate to summarize in 30 seconds. Push for bottom-line impact."
    ),
    "probing": (
        "You are a deeply skeptical, detail-oriented interviewer. Question every claim. "
        "Ask for evidence, numbers, and specifics behind every statement. Probe motives: "
        "why did you make that decision? What would you do differently? Don't accept "
        "surface-level answers."
    ),
}


def _build_behavioral_system_prompt(session, questions: list) -> str:
    persona_key = session.behavioral_persona.value if session.behavioral_persona else "supportive"
    persona = _BEHAVIORAL_PERSONA.get(persona_key, _BEHAVIORAL_PERSONA["supportive"])
    duration = session.duration_minutes

    question_list = "\n".join(
        f"{i + 1}. {q.prompt}" for i, q in enumerate(questions)
    )

    return f"""{persona}

You are conducting a behavioral mock interview. The session lasts approximately {duration} minutes.

Interview plan — ask these questions in order, then follow up naturally based on the candidate's responses:
{question_list}

Conduct guidelines:
- Open with a brief professional greeting and one sentence describing the format.
- Ask one question at a time. Wait for a complete response before moving on.
- If an answer is missing the Situation, Task, Action, or Result component — ask specifically for the missing piece.
- If an answer is vague or lacks a concrete example, ask a targeted follow-up (e.g., "Can you walk me through a specific moment?" or "What was the measurable outcome?").
- Do not skip questions unless time is clearly running out.
- Close the interview professionally once all questions are covered or time is nearly up.
- Stay in character throughout. Do not break the fourth wall or mention that you are an AI."""


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
- Stay in character throughout — do not break the fourth wall or mention that you are an AI.
- You have two background tools for technical interviews. Tool calls are completely silent — never mention them, never say their names, never say you are "calling a tool" or "looking at the code now". Just use the result naturally in your response.
  * NEVER ask the candidate to read, paste, or describe their code aloud. You can retrieve it yourself.
  * NEVER say "could you share your code" or "walk me through what you wrote".
  * Silently call get_current_code and use the result whenever:
    - The candidate says anything like "I'm done", "finished", "ready", "let me know what you think", "does this make sense", "is this right", "does this look good", or asks for feedback or a hint
    - You are about to comment on their approach or implementation
    - The candidate has been silent for more than two minutes
  * Silently call get_test_results and use the result whenever:
    - The candidate mentions running or submitting their code
    - The candidate asks why their code isn't working or what the results look like
- When reviewing code, act like a real interviewer: ask guiding questions and give directional hints only. Never reveal the solution or write correct code for them. If their approach is wrong, point them toward rethinking a specific part ("have you considered what happens when..."). If their approach is right but incomplete, ask what edge cases they might be missing. Keep code feedback concise — one observation at a time."""




async def create_interview_agent(session, questions: list) -> tuple[str, str, dict]:
    """Create a per-session ElevenLabs conversational agent. Returns (agent_id, first_message, voice_cfg)."""
    tone_key = session.interviewer_tone.value if session.interviewer_tone else "neutral"
    voice_cfg = _TONE_VOICE.get(tone_key, _TONE_VOICE["neutral"])

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
                "tools": [
                    {
                        "type": "client",
                        "name": "get_current_code",
                        "description": "Returns the candidate's current code and the programming language they selected. Call this whenever you need to see the code — never ask the candidate to share it verbally.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                    {
                        "type": "client",
                        "name": "get_test_results",
                        "description": "Returns the latest test case run results: how many passed, how many failed, and the output for each. Call this after the candidate runs or submits their code.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                ],
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
                "voice_id": voice_cfg["voice_id"],
                "optimize_streaming_latency": 3,
                "stability": voice_cfg["stability"],
                "similarity_boost": voice_cfg["similarity_boost"],
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
        return resp.json()["agent_id"], first_message, voice_cfg


async def create_behavioral_agent(session, questions: list) -> tuple[str, str, dict]:
    """Create a per-session ElevenLabs agent for behavioral interviews. Returns (agent_id, first_message, voice_cfg)."""
    persona_key = session.behavioral_persona.value if session.behavioral_persona else "supportive"
    voice_cfg = _BEHAVIORAL_VOICE.get(persona_key, _BEHAVIORAL_VOICE["supportive"])

    first_message = (
        f"Hello! Thank you for joining today. I'll be conducting your behavioral interview — "
        f"we have about {session.duration_minutes} minutes. "
        f"I'll ask you several questions about past experiences. Please use specific examples. "
        f"Let's get started — could you briefly tell me about yourself and your background?"
    )

    payload = {
        "name": f"BehavioralInterviewer-{session.id}",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": _build_behavioral_system_prompt(session, questions),
                    "llm": "gemini-2.0-flash-001",
                    "temperature": 0.6,
                },
                "first_message": first_message,
                "language": "en",
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
                "voice_id": voice_cfg["voice_id"],
                "optimize_streaming_latency": 3,
                "stability": voice_cfg["stability"],
                "similarity_boost": voice_cfg["similarity_boost"],
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
            raise RuntimeError(f"ElevenLabs behavioral agent creation failed {resp.status_code}: {resp.text}")
        return resp.json()["agent_id"], first_message, voice_cfg


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
