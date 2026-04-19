from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from auth.clerk import require_auth
from schemas.companies import CompanySnapshotResponse, ThemeScoreResponse
from services.company_research import _is_fresh, get_or_fetch_snapshot

router = APIRouter(prefix="/api/companies", tags=["companies"])


def _doc_to_response(doc: dict) -> CompanySnapshotResponse:
    retrieved_at = doc.get("retrieved_at") or datetime.now(timezone.utc)
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

    return CompanySnapshotResponse(
        company=doc["company"],
        role=doc.get("role"),
        behavioral_themes=[
            ThemeScoreResponse(theme=t["theme"], confidence=t["confidence"])
            for t in doc.get("behavioral_themes", [])
        ],
        technical_focus=[
            ThemeScoreResponse(theme=t["theme"], confidence=t["confidence"])
            for t in doc.get("technical_focus", [])
        ],
        style_signals=[
            ThemeScoreResponse(theme=t["theme"], confidence=t["confidence"])
            for t in doc.get("style_signals", [])
        ],
        retrieved_at=retrieved_at,
        is_fresh=_is_fresh(retrieved_at),
    )


@router.get("/{company}/snapshot", response_model=CompanySnapshotResponse)
async def get_company_snapshot(
    company: str,
    role: str | None = Query(default=None, description="Job role for more targeted research"),
    clerk_user_id: str = Depends(require_auth),
):
    doc = await get_or_fetch_snapshot(company, role)
    return _doc_to_response(doc)
