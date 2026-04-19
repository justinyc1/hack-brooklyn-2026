import json
import logging
from datetime import datetime, timedelta, timezone

import httpx

from config import settings
from db import db
from models.company_snapshot import CompanySnapshot, ThemeScore
from services.llm import chat_complete

logger = logging.getLogger(__name__)

SNAPSHOT_TTL_DAYS = 7
TAVILY_URL = "https://api.tavily.com/search"

_SYNTHESIS_PROMPT = """\
You are analyzing interview data for {company} ({role} role) collected from web sources.

Source snippets:
{snippets}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "behavioral_themes": [
    {{"theme": "<theme description>", "confidence": <float 0.0-1.0>}},
    ...
  ],
  "technical_focus": [
    {{"theme": "<topic>", "confidence": <float 0.0-1.0>}},
    ...
  ],
  "style_signals": [
    {{"theme": "<signal about interview style or format>", "confidence": <float 0.0-1.0>}},
    ...
  ]
}}

Include up to 5 items per category. Confidence reflects how strongly the sources support the theme."""


def _is_fresh(retrieved_at: datetime) -> bool:
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - retrieved_at
    return age < timedelta(days=SNAPSHOT_TTL_DAYS)


async def _tavily_search(query: str, include_domains: list[str] | None = None) -> list[dict]:
    """Single Tavily search. Returns list of result dicts with title+content. Raises on HTTP error."""
    payload: dict = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 5,
    }
    if include_domains:
        payload["include_domains"] = include_domains

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(TAVILY_URL, json=payload)
        resp.raise_for_status()
        return resp.json().get("results", [])


def _extract_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in LLM response")
    return json.loads(raw[start:end])


async def fetch_snapshot(company: str, role: str | None) -> dict:
    """Call Tavily + LLM to build a fresh snapshot dict. Never raises — returns empty on failure."""
    role_str = role or "software engineer"
    try:
        broad_results = await _tavily_search(
            f"{company} {role_str} software engineer interview questions behavioral technical"
        )
        leetbot_results = await _tavily_search(
            f"{company} interview questions",
            include_domains=["leetbot.org"],
        )
        all_results = broad_results + leetbot_results
    except Exception:
        logger.exception("Tavily search failed for company=%s role=%s", company, role_str)
        return {
            "company": company,
            "role": role,
            "behavioral_themes": [],
            "technical_focus": [],
            "style_signals": [],
        }

    snippets = "\n\n".join(
        f"[{r.get('title', 'Source')}]\n{r.get('content', '')}"
        for r in all_results[:8]
    )

    try:
        prompt = _SYNTHESIS_PROMPT.format(
            company=company,
            role=role_str,
            snippets=snippets or "(no sources found)",
        )
        raw = await chat_complete(prompt)
        parsed = _extract_json(raw)
        return {
            "company": company,
            "role": role,
            "behavioral_themes": parsed.get("behavioral_themes", []),
            "technical_focus": parsed.get("technical_focus", []),
            "style_signals": parsed.get("style_signals", []),
        }
    except Exception:
        logger.exception("LLM synthesis failed for company=%s", company)
        return {
            "company": company,
            "role": role,
            "behavioral_themes": [],
            "technical_focus": [],
            "style_signals": [],
        }


async def get_or_fetch_snapshot(company: str, role: str | None) -> dict:
    """Return cached snapshot if fresh, otherwise fetch new one and cache it."""
    query: dict = {"company": company, "role": role}

    try:
        cached = db.company_snapshots.find_one(query)
        if cached:
            retrieved_at = cached.get("retrieved_at")
            if retrieved_at and _is_fresh(retrieved_at):
                logger.debug("Returning cached snapshot for %s / %s", company, role)
                return cached
    except Exception:
        logger.exception("DB read failed for company=%s role=%s", company, role)

    data = await fetch_snapshot(company, role)
    snapshot = CompanySnapshot(
        company=data["company"],
        role=data["role"],
        behavioral_themes=[ThemeScore(**t) for t in data["behavioral_themes"]],
        technical_focus=[ThemeScore(**t) for t in data["technical_focus"]],
        style_signals=[ThemeScore(**t) for t in data["style_signals"]],
        retrieved_at=datetime.now(timezone.utc),
    )
    doc = snapshot.to_mongo()

    try:
        db.company_snapshots.replace_one(query, doc, upsert=True)
        logger.info("Cached new snapshot for company=%s role=%s", company, role)
    except Exception:
        logger.exception("Failed to cache snapshot for company=%s role=%s", company, role)

    return {
        "company": data["company"],
        "role": data["role"],
        "behavioral_themes": data["behavioral_themes"],
        "technical_focus": data["technical_focus"],
        "style_signals": data["style_signals"],
        "retrieved_at": snapshot.retrieved_at,
    }
