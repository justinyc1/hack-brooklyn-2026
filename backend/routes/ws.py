"""WebSocket gateway for live interview session state.

The frontend connects here for server-driven events (question changes, timer,
transcript sync notifications). Audio/voice goes directly to ElevenLabs via
their SDK — this channel handles only session orchestration events.

Auth: pass the Clerk session token as the `token` query parameter, since
browsers cannot send custom headers on WebSocket connections.
"""

import json
import logging
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from auth.clerk import verify_token
from db import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# session_id → list of active WebSocket connections
_connections: dict[str, list[WebSocket]] = {}


async def broadcast(session_id: str, event: dict[str, Any]) -> None:
    """Push an event to every client connected to a session."""
    dead: list[WebSocket] = []
    for ws in _connections.get(session_id, []):
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _remove(session_id, ws)


def _remove(session_id: str, ws: WebSocket) -> None:
    bucket = _connections.get(session_id, [])
    if ws in bucket:
        bucket.remove(ws)
    if not bucket:
        _connections.pop(session_id, None)


@router.websocket("/ws/interviews/{session_id}")
async def interview_ws(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(..., description="Clerk session JWT"),
):
    # --- Auth ---
    try:
        claims = verify_token(token)
        clerk_user_id: str = claims["sub"]
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # --- Session ownership check ---
    if not ObjectId.is_valid(session_id):
        await websocket.close(code=4004, reason="Invalid session id")
        return

    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()

    _connections.setdefault(session_id, []).append(websocket)
    logger.info("WS connected: session=%s user=%s", session_id, clerk_user_id)

    # Send current session state immediately on connect
    await websocket.send_json({
        "type": "session.state",
        "session_id": session_id,
        "status": doc.get("status"),
        "question_ids": doc.get("question_ids", []),
        "elevenlabs_agent_id": doc.get("elevenlabs_agent_id"),
        "elevenlabs_conversation_id": doc.get("elevenlabs_conversation_id"),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue
            await _handle(session_id, clerk_user_id, msg, websocket)

    except WebSocketDisconnect:
        _remove(session_id, websocket)
        logger.info("WS disconnected: session=%s user=%s", session_id, clerk_user_id)


async def _handle(session_id: str, clerk_user_id: str, msg: dict, ws: WebSocket) -> None:
    msg_type = msg.get("type")

    if msg_type == "ping":
        await ws.send_json({"type": "pong"})

    elif msg_type == "conversation.started":
        # Frontend sends this once ElevenLabs fires onConnect with conversation_id
        conversation_id = msg.get("conversation_id")
        if conversation_id:
            db.sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"elevenlabs_conversation_id": conversation_id}},
            )
            await broadcast(session_id, {
                "type": "conversation.linked",
                "session_id": session_id,
                "conversation_id": conversation_id,
            })

    elif msg_type == "question.advance":
        # Broadcast to all clients so UI stays in sync
        await broadcast(session_id, {
            "type": "question.advanced",
            "session_id": session_id,
            "question_index": msg.get("question_index"),
        })

    elif msg_type == "transcript.synced":
        await broadcast(session_id, {
            "type": "transcript.synced",
            "session_id": session_id,
            "segment_count": msg.get("segment_count"),
        })

    else:
        await ws.send_json({"type": "error", "detail": f"Unknown message type: {msg_type}"})
