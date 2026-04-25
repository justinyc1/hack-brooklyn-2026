import pytest
from datetime import datetime, timezone
from models.feedback import FeedbackReport, CategoryScores, QuestionFeedback, EvidenceSpan
from models.interview_session import InterviewSession, InterviewMode, InterviewerTone, Difficulty


def _make_report(**overrides) -> FeedbackReport:
    defaults = dict(
        session_id="sess1",
        overall_score=7.5,
        category_scores=CategoryScores(clarity=8.0, confidence=7.0, problem_solving=8.5),
        per_question_feedback=[
            QuestionFeedback(
                question_id="q1",
                question_text="Explain binary search.",
                score=7.5,
                strengths=["Good explanation"],
                improvements=["Missed edge case"],
                better_answer_example="Use lo/hi pointers to find mid.",
            )
        ],
        top_strengths=["Clear communication"],
        top_weaknesses=["Edge case handling"],
        targeted_drills=["Practice: Edge cases in binary search"],
        generated_at=datetime(2026, 4, 25, 12, 0, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return FeedbackReport(**defaults)


def _make_session() -> InterviewSession:
    return InterviewSession(
        clerk_user_id="user_123",
        mode=InterviewMode.technical,
        role="Software Engineer",
        company="Acme Corp",
        difficulty=Difficulty.medium,
        interviewer_tone=InterviewerTone.neutral,
        duration_minutes=45,
    )


def test_generate_feedback_html_is_valid_html():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>")


def test_generate_feedback_html_contains_overall_score():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    # overall_score 7.5 → displayed as 75
    assert "75" in html


def test_generate_feedback_html_contains_session_info():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    assert "Software Engineer" in html
    assert "Acme Corp" in html


def test_generate_feedback_html_without_session():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), None)
    assert html.startswith("<!DOCTYPE html>")
    assert "75" in html


def test_generate_feedback_html_contains_strengths_and_weaknesses():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    assert "Clear communication" in html
    assert "Edge case handling" in html


def test_generate_feedback_html_contains_question_text():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    assert "Explain binary search." in html


def test_generate_feedback_html_contains_targeted_drills():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    assert "Edge cases in binary search" in html


def test_generate_feedback_html_contains_better_answer():
    from services.report_generator import generate_feedback_html
    html = generate_feedback_html(_make_report(), _make_session())
    assert "Use lo/hi pointers to find mid." in html


def test_generate_feedback_html_omits_null_category_scores():
    from services.report_generator import generate_feedback_html
    # CategoryScores with only clarity set; all others None
    report = _make_report(category_scores=CategoryScores(clarity=9.0))
    html = generate_feedback_html(report, None)
    # "Clarity" should appear as a category label
    assert "Clarity" in html
    # "Confidence" should not appear (it's None)
    assert "Confidence" not in html
