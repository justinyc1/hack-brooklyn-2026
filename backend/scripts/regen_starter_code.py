"""
Regenerate test cases + starter code for all problems in MongoDB.
Skips the 12 hand-crafted local problems. Run from backend/:
    python scripts/regen_starter_code.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import db
from services.leetcode_client import fetch_problem_detail
from services.leetcode_html_parser import parse_question_html
from services.test_case_generator import generate_full_problem

LOCAL_IDS = {
    "two-sum", "valid-parentheses", "climbing-stairs",
    "best-time-to-buy-and-sell-stock", "contains-duplicate",
    "maximum-subarray", "longest-substring-without-repeating-characters",
    "product-of-array-except-self", "coin-change",
    "find-minimum-in-rotated-sorted-array", "trapping-rain-water",
    "longest-valid-parentheses",
}


async def regen(slug: str) -> bool:
    detail = await fetch_problem_detail(slug)
    if not detail:
        print(f"  [skip] could not fetch detail for {slug}")
        return False

    parsed = parse_question_html(detail.get("question_html", ""))
    description = parsed["description"] or detail.get("description", "")

    problem_input = {
        "title": detail["title"],
        "description": description,
        "examples": parsed["examples"],
        "constraints": parsed["constraints"],
    }

    generated = await generate_full_problem(problem_input)
    if not generated:
        print(f"  [fail] LLM generation failed for {slug}")
        return False

    doc = {
        "id": slug,
        "title": detail["title"],
        "difficulty": detail["difficulty"].lower(),
        "description": description,
        "examples": parsed["examples"],
        "constraints": parsed["constraints"],
        "topic_tags": detail.get("topic_tags", []),
        "test_cases": generated["test_cases"],
        "starter_code": generated["starter_code"],
    }

    db.problems.update_one({"id": slug}, {"$set": doc}, upsert=True)
    print(f"  [ok] {slug}")
    return True


async def main():
    docs = list(db.problems.find({"test_cases": {"$exists": True}}, {"id": 1, "_id": 0}))
    targets = [d["id"] for d in docs if d["id"] not in LOCAL_IDS]

    if not targets:
        print("No LLM-generated problems found in MongoDB.")
        return

    print(f"Regenerating {len(targets)} problem(s)...")
    ok = 0
    for slug in targets:
        print(f"  {slug}...")
        if await regen(slug):
            ok += 1

    print(f"\nDone: {ok}/{len(targets)} regenerated.")


if __name__ == "__main__":
    asyncio.run(main())
