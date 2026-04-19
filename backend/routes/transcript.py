from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth.clerk import require_auth
from db import db
from models.transcript import TranscriptSegment
from schemas.transcript import (
    AddSegmentRequest,
    SegmentResponse,
    TranscriptByQuestionResponse,
    TranscriptResponse,
)

router = APIRouter(prefix="/api/interviews/{session_id}/transcript", tags=["transcript"])


def _require_session_owner(session_id: str, clerk_user_id: str) -> dict:
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    doc = db.sessions.find_one({"_id": ObjectId(session_id), "clerk_user_id": clerk_user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return doc


def _segment_to_response(seg: TranscriptSegment) -> SegmentResponse:
    return SegmentResponse(
        id=seg.id,
        session_id=seg.session_id,
        question_id=seg.question_id,
        speaker=seg.speaker,
        text=seg.text,
        is_partial=seg.is_partial,
        timestamp=seg.timestamp,
    )


@router.post("", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
def add_segment(
    session_id: str,
    body: AddSegmentRequest,
    clerk_user_id: str = Depends(require_auth),
):
    _require_session_owner(session_id, clerk_user_id)

    segment = TranscriptSegment(
        session_id=session_id,
        question_id=body.question_id,
        speaker=body.speaker,
        text=body.text,
        is_partial=body.is_partial,
    )

    result = db.transcripts.insert_one(segment.to_mongo())
    doc = db.transcripts.find_one({"_id": result.inserted_id})
    return _segment_to_response(TranscriptSegment.from_mongo(doc))


@router.get("", response_model=TranscriptResponse | TranscriptByQuestionResponse)
def get_transcript(
    session_id: str,
    clerk_user_id: str = Depends(require_auth),
    by_question: bool = Query(default=False, description="Group segments by question_id"),
    include_partial: bool = Query(default=False, description="Include partial (in-progress) segments"),
):
    _require_session_owner(session_id, clerk_user_id)

    query: dict = {"session_id": session_id}
    if not include_partial:
        query["is_partial"] = False

    docs = list(db.transcripts.find(query).sort("timestamp", 1))
    segments = [_segment_to_response(TranscriptSegment.from_mongo(d)) for d in docs]

    if by_question:
        grouped: dict[str, list[SegmentResponse]] = {}
        unattributed: list[SegmentResponse] = []
        for seg in segments:
            if seg.question_id:
                grouped.setdefault(seg.question_id, []).append(seg)
            else:
                unattributed.append(seg)
        return TranscriptByQuestionResponse(
            session_id=session_id,
            by_question=grouped,
            unattributed=unattributed,
        )

    return TranscriptResponse(session_id=session_id, segments=segments, total=len(segments))
