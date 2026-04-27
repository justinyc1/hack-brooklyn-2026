import logging
import time

import httpx

from services.html_utils import strip_html

logger = logging.getLogger(__name__)

_BASE = "https://alfa-leetcode-api.onrender.com"
_LIST_CACHE_TTL = 3600    # 1 hour
_DETAIL_CACHE_TTL = 21600  # 6 hours

_list_cache: list[dict] | None = None
_list_cache_at: float = 0.0
_detail_cache: dict[str, dict] = {}
_detail_cache_at: dict[str, float] = {}


async def fetch_problem_list(limit: int = 200) -> list[dict]:
    """Return raw problem list items from alfa-leetcode-api, with in-memory caching."""
    global _list_cache, _list_cache_at
    now = time.time()
    if _list_cache is not None and now - _list_cache_at < _LIST_CACHE_TTL:
        return _list_cache

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(f"{_BASE}/problems", params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
        result = data.get("problemsetQuestionList", [])
        _list_cache = result
        _list_cache_at = now
        return result
    except Exception as exc:
        logger.error("Failed to fetch LeetCode problem list: %s", exc)
        return _list_cache or []


async def fetch_problem_detail(slug: str) -> dict | None:
    """Return enriched problem detail for a titleSlug, with in-memory caching.

    Returns None on error. Returned dict keys: title, titleSlug, difficulty,
    description, topic_tags, hints.
    """
    now = time.time()
    if slug in _detail_cache and now - _detail_cache_at.get(slug, 0.0) < _DETAIL_CACHE_TTL:
        return _detail_cache[slug]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(f"{_BASE}/select", params={"titleSlug": slug})
            resp.raise_for_status()
            data = resp.json()

        raw_html = data.get("question", data.get("content", ""))
        result = {
            "title": data.get("questionTitle", data.get("title", "")),
            "titleSlug": data.get("titleSlug", slug),
            "difficulty": data.get("difficulty", ""),
            "description": strip_html(raw_html),
            "topic_tags": [t["name"] for t in data.get("topicTags", [])],
            "hints": data.get("hints", []),
            "example_testcases": data.get("exampleTestcases", ""),
            "question_html": raw_html,
        }
        _detail_cache[slug] = result
        _detail_cache_at[slug] = now
        return result
    except Exception as exc:
        logger.error("Failed to fetch LeetCode detail for %s: %s", slug, exc)
        return None
