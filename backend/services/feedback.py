import asyncio
import copy
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone

from bson import ObjectId

from db import db
from models.feedback import CategoryScores, EvidenceSpan, FeedbackReport, QuestionFeedback
from services.llm import chat_complete

logger = logging.getLogger(__name__)

_BEHAVIORAL_PROMPT = """\
You are evaluating a mock software engineering interview response.

Question type: behavioral
Question: {question}

Candidate response:
{transcript}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "score": <float 0-10>,
  "strengths": [<string>, ...],
  "improvements": [<string>, ...],
  "better_answer_example": <string>,
  "category_scores": {{
    "clarity": <float 0-10>,
    "confidence": <float 0-10>,
    "conciseness": <float 0-10>,
    "structure": <float 0-10>,
    "specificity": <float 0-10>,
    "star_structure": <float 0-10>,
    "impact_articulation": <float 0-10>,
    "ownership": <float 0-10>
  }},
  "evidence_quotes": [<string>, ...]
}}"""

_TECHNICAL_PROMPT = """\
You are evaluating a mock software engineering technical interview response.

Question type: technical
Question: {question}

Candidate verbal explanation:
{transcript}

Code submitted ({language}):
{code}

Test results: {passed_count}/{total_count} passed, status: {status}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "score": <float 0-10>,
  "strengths": [<string>, ...],
  "improvements": [<string>, ...],
  "better_answer_example": <string>,
  "category_scores": {{
    "clarity": <float 0-10>,
    "confidence": <float 0-10>,
    "conciseness": <float 0-10>,
    "structure": <float 0-10>,
    "specificity": <float 0-10>,
    "problem_solving": <float 0-10>,
    "code_correctness": <float 0-10>,
    "optimization_awareness": <float 0-10>
  }},
  "evidence_quotes": [<string>, ...]
}}"""

_FALLBACK_RESULT = {
    "score": 5.0,
    "strengths": [],
    "improvements": [],
    "better_answer_example": None,
    "category_scores": {},
    "evidence_quotes": [],
}


def _transcript_text(segments: list[dict]) -> str:
    return "\n".join(
        f"[{s['speaker'].upper()}] {s['text']}"
        for s in segments
        if not s.get("is_partial")
    )


def _extract_json(raw: str) -> dict:
    """Extract the first JSON object from an LLM response."""
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(raw[start:end])


async def score_question(
    question: dict,
    segments: list[dict],
    code_submission: dict | None,
) -> dict:
    """Call LLM to score one question. Returns a result dict. Never raises."""
    transcript = _transcript_text(segments)
    if not transcript.strip():
        transcript = "(no response recorded)"

    try:
        if question.get("type") == "technical":
            prompt = _TECHNICAL_PROMPT.format(
                question=question["prompt"],
                transcript=transcript,
                language=code_submission.get("language", "unknown") if code_submission else "unknown",
                code=code_submission.get("code", "(no code submitted)") if code_submission else "(no code submitted)",
                passed_count=code_submission.get("passed_count", 0) if code_submission else 0,
                total_count=code_submission.get("total_count", 0) if code_submission else 0,
                status=code_submission.get("status", "not submitted") if code_submission else "not submitted",
            )
        else:
            prompt = _BEHAVIORAL_PROMPT.format(
                question=question["prompt"],
                transcript=transcript,
            )

        raw = await chat_complete(prompt)
        return _extract_json(raw)

    except Exception:
        logger.exception("LLM scoring failed for question %s", question.get("_id"))
        return copy.deepcopy(_FALLBACK_RESULT)


def aggregate_question_scores(per_question_results: list[dict]) -> dict:
    """Average per-question scores into overall metrics."""
    if not per_question_results:
        return {
            "overall_score": 0.0,
            "category_scores": {},
            "all_strengths": [],
            "all_improvements": [],
        }

    overall_score = sum(r["score"] for r in per_question_results) / len(per_question_results)

    category_buckets: dict[str, list[float]] = defaultdict(list)
    all_strengths: list[str] = []
    all_improvements: list[str] = []

    for r in per_question_results:
        for k, v in r.get("category_scores", {}).items():
            if isinstance(v, (int, float)):
                category_buckets[k].append(float(v))
        all_strengths.extend(r.get("strengths", []))
        all_improvements.extend(r.get("improvements", []))

    category_scores = {k: sum(v) / len(v) for k, v in category_buckets.items()}

    return {
        "overall_score": round(overall_score, 2),
        "category_scores": category_scores,
        "all_strengths": all_strengths,
        "all_improvements": all_improvements,
    }


async def generate_feedback(session_id: str) -> None:
    """Full feedback pipeline. Called as a background task on session completion."""
    try:
        await _run_feedback_pipeline(session_id)
    except Exception:
        logger.exception("Feedback pipeline failed for session %s", session_id)


async def _run_feedback_pipeline(session_id: str) -> None:
    # DB calls here are synchronous PyMongo (blocking). This is acceptable because
    # this function only runs as a background task after session completion, not on
    # the request path. Do not copy this pattern into request handlers.
    session_doc = db.sessions.find_one({"_id": ObjectId(session_id)})
    if not session_doc:
        logger.warning("generate_feedback: session %s not found", session_id)
        return

    question_ids = session_doc.get("question_ids", [])
    valid_oids = []
    for qid in question_ids:
        try:
            valid_oids.append(ObjectId(qid))
        except Exception:
            pass
    questions = list(db.questions.find({"_id": {"$in": valid_oids}}))
    questions.sort(key=lambda q: q.get("order", 0))

    all_segments = list(db.transcripts.find({"session_id": session_id, "is_partial": False}))

    # Group segments by question_id
    segments_by_question: dict[str, list[dict]] = defaultdict(list)
    for seg in all_segments:
        qid = seg.get("question_id")
        if qid:
            segments_by_question[qid].append(seg)

    # Load final code submissions keyed by question_id
    code_submissions = {
        doc["question_id"]: doc
        for doc in db.code_submissions.find({"session_id": session_id, "is_final": True})
    }

    # --- Score all questions concurrently ---
    qids = [str(q["_id"]) for q in questions]
    per_question_results: list[dict] = await asyncio.gather(*[
        score_question(q, segments_by_question.get(str(q["_id"]), []), code_submissions.get(str(q["_id"])))
        for q in questions
    ])

    question_feedback_list: list[QuestionFeedback] = []
    for q, qid, result in zip(questions, qids, per_question_results):
        evidence = [
            EvidenceSpan(
                transcript_segment_id="",
                quote=quote,
                note="",
            )
            for quote in result.get("evidence_quotes", [])[:3]
        ]
        question_feedback_list.append(QuestionFeedback(
            question_id=qid,
            score=result["score"],
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            better_answer_example=result.get("better_answer_example"),
            evidence=evidence,
        ))

    # --- Aggregate ---
    agg = aggregate_question_scores(per_question_results)

    cs_data = agg["category_scores"]
    category_scores = CategoryScores(
        clarity=cs_data.get("clarity"),
        confidence=cs_data.get("confidence"),
        conciseness=cs_data.get("conciseness"),
        structure=cs_data.get("structure"),
        specificity=cs_data.get("specificity"),
        pace=cs_data.get("pace"),
        problem_solving=cs_data.get("problem_solving"),
        code_correctness=cs_data.get("code_correctness"),
        optimization_awareness=cs_data.get("optimization_awareness"),
        star_structure=cs_data.get("star_structure"),
        impact_articulation=cs_data.get("impact_articulation"),
        ownership=cs_data.get("ownership"),
    )

    top_strengths = list(dict.fromkeys(agg["all_strengths"]))[:5]
    top_weaknesses = list(dict.fromkeys(agg["all_improvements"]))[:5]
    targeted_drills = [f"Practice: {w}" for w in top_weaknesses[:3]]

    report = FeedbackReport(
        session_id=session_id,
        overall_score=agg["overall_score"],
        category_scores=category_scores,
        per_question_feedback=question_feedback_list,
        top_strengths=top_strengths,
        top_weaknesses=top_weaknesses,
        targeted_drills=targeted_drills,
        generated_at=datetime.now(timezone.utc),
    )

    db.feedback.replace_one(
        {"session_id": session_id},
        report.to_mongo(),
        upsert=True,
    )
    logger.info("Feedback report saved for session %s", session_id)

    # --- Broadcast WS event ---
    try:
        from routes.ws import broadcast
        await broadcast(session_id, {
            "type": "feedback.generated",
            "session_id": session_id,
        })
    except Exception:
        logger.warning("WS broadcast failed for feedback.generated on session %s", session_id)
