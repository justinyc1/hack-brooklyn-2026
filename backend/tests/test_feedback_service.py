import json
import pytest
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_question(qid: str, qtype: str, prompt: str, coding_problem_id=None):
    return {
        "_id": qid,
        "session_id": "sess1",
        "order": 0,
        "type": qtype,
        "prompt": prompt,
        "follow_up_tree": [],
        "coding_problem_id": coding_problem_id,
    }


def _make_segment(speaker: str, text: str, question_id: str = None):
    return {
        "_id": "seg1",
        "session_id": "sess1",
        "question_id": question_id,
        "speaker": speaker,
        "text": text,
        "is_partial": False,
        "timestamp": "2026-01-01T00:00:00Z",
    }


BEHAVIORAL_LLM_RESPONSE = json.dumps({
    "score": 7.5,
    "strengths": ["Clear STAR structure", "Concrete impact metrics"],
    "improvements": ["Add more reflection on outcome"],
    "better_answer_example": "I led the team to deliver X by doing Y, resulting in Z.",
    "category_scores": {
        "clarity": 8.0,
        "confidence": 7.0,
        "conciseness": 7.5,
        "structure": 8.0,
        "specificity": 7.0,
        "star_structure": 7.5,
        "impact_articulation": 8.0,
        "ownership": 7.0,
    },
    "evidence_quotes": ["I led the backend refactor"],
})

TECHNICAL_LLM_RESPONSE = json.dumps({
    "score": 8.0,
    "strengths": ["Optimal O(n) solution", "Explained approach clearly"],
    "improvements": ["Didn't discuss space complexity"],
    "better_answer_example": "I would use a hash map to achieve O(n) time and O(n) space.",
    "category_scores": {
        "clarity": 8.0,
        "confidence": 8.5,
        "conciseness": 7.5,
        "structure": 8.0,
        "specificity": 8.0,
        "problem_solving": 9.0,
        "code_correctness": 8.0,
        "optimization_awareness": 7.0,
    },
    "evidence_quotes": ["I'll use a hash map here"],
})


# ---------------------------------------------------------------------------
# Tests: score_question
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_score_question_behavioral_returns_parsed_result():
    from services.feedback import score_question

    question = _make_question("q1", "behavioral", "Tell me about a challenge.")
    segments = [_make_segment("user", "I faced a bug in prod...", question_id="q1")]
    code_submission = None

    with patch("services.feedback.chat_complete", new=AsyncMock(return_value=BEHAVIORAL_LLM_RESPONSE)):
        result = await score_question(question, segments, code_submission)

    assert result["score"] == 7.5
    assert "Clear STAR structure" in result["strengths"]
    assert result["category_scores"]["star_structure"] == 7.5


@pytest.mark.asyncio
async def test_score_question_technical_includes_code_in_prompt():
    from services.feedback import score_question

    question = _make_question("q2", "technical", "Find two numbers that sum to target.", coding_problem_id="two-sum")
    segments = [_make_segment("user", "I'll use a hash map here.", question_id="q2")]
    code_submission = {
        "language": "python",
        "code": "def twoSum(nums, target): pass",
        "passed_count": 3,
        "total_count": 4,
        "status": "wrong_answer",
    }

    captured_prompt: list[str] = []

    async def capture(prompt: str) -> str:
        captured_prompt.append(prompt)
        return TECHNICAL_LLM_RESPONSE

    with patch("services.feedback.chat_complete", new=capture):
        result = await score_question(question, segments, code_submission)

    assert "hash map" in captured_prompt[0]
    assert "python" in captured_prompt[0]
    assert "def twoSum" in captured_prompt[0]
    assert result["score"] == 8.0
    assert result["category_scores"]["problem_solving"] == 9.0


@pytest.mark.asyncio
async def test_score_question_returns_defaults_on_llm_failure():
    from services.feedback import score_question

    question = _make_question("q3", "behavioral", "Describe a conflict.")
    segments = [_make_segment("user", "I had a disagreement...", question_id="q3")]

    with patch("services.feedback.chat_complete", new=AsyncMock(side_effect=Exception("API down"))):
        result = await score_question(question, segments, None)

    assert result["score"] == 5.0
    assert result["strengths"] == []
    assert result["improvements"] == []


@pytest.mark.asyncio
async def test_score_question_returns_defaults_on_malformed_json():
    from services.feedback import score_question

    question = _make_question("q4", "behavioral", "Describe a conflict.")
    segments = [_make_segment("user", "I had a disagreement...", question_id="q4")]

    with patch("services.feedback.chat_complete", new=AsyncMock(return_value="not valid json at all")):
        result = await score_question(question, segments, None)

    assert result["score"] == 5.0
    assert result["strengths"] == []
    assert result["improvements"] == []


# ---------------------------------------------------------------------------
# Tests: aggregate_question_scores
# ---------------------------------------------------------------------------

def test_aggregate_scores_averages_correctly():
    from services.feedback import aggregate_question_scores

    per_q = [
        {
            "score": 6.0,
            "category_scores": {"clarity": 6.0, "confidence": 7.0},
            "strengths": ["A"],
            "improvements": ["B"],
        },
        {
            "score": 8.0,
            "category_scores": {"clarity": 8.0, "confidence": 9.0},
            "strengths": ["C"],
            "improvements": ["D"],
        },
    ]

    result = aggregate_question_scores(per_q)

    assert result["overall_score"] == pytest.approx(7.0)
    assert result["category_scores"]["clarity"] == pytest.approx(7.0)
    assert result["category_scores"]["confidence"] == pytest.approx(8.0)
    assert "A" in result["all_strengths"]
    assert "C" in result["all_strengths"]
    assert "B" in result["all_improvements"]


def test_aggregate_scores_handles_missing_categories():
    from services.feedback import aggregate_question_scores

    per_q = [
        {"score": 7.0, "category_scores": {"clarity": 7.0}, "strengths": [], "improvements": []},
        {"score": 7.0, "category_scores": {"confidence": 8.0}, "strengths": [], "improvements": []},
    ]

    result = aggregate_question_scores(per_q)
    assert result["category_scores"]["clarity"] == pytest.approx(7.0)
    assert result["category_scores"]["confidence"] == pytest.approx(8.0)
