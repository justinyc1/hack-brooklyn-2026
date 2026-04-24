"""Generates a question plan for a session.

Behavioral mode: LLM-generated STAR questions (Groq primary, Featherless fallback).
Technical mode: static problem stubs (unchanged).
"""

import json
import logging
import random
import re

from models.interview_session import Difficulty, InterviewMode
from models.question import Question, QuestionType
from services.code_runner import load_all_problems
from services.llm import chat_complete

logger = logging.getLogger(__name__)

_BEHAVIORAL_QUESTION_PROMPT = """\
Generate exactly {n} distinct behavioral interview questions for a software engineering candidate.

Requirements:
- Each question must be in STAR style — asking the candidate to describe a specific past experience
- Cover DIFFERENT topics — pick from this pool without repeating: leadership and ownership, conflict resolution, failure and learning, teamwork and collaboration, working under time pressure, navigating ambiguity, taking initiative, receiving and acting on feedback, cross-functional communication, delivering measurable impact
- Do NOT use overused openers like "Tell me about yourself" or "What is your greatest weakness"
- Make questions specific, probing, and varied in length and complexity
- Each question should be a single sentence ending with a period or question mark

Return ONLY valid JSON with this exact structure (no markdown code fences, no explanation):
{{"questions": ["question 1", "question 2", ...]}}

Generate {n} questions now."""


def _question_count(duration_minutes: int) -> int:
    if duration_minutes <= 20:
        return 2
    if duration_minutes <= 30:
        return 3
    if duration_minutes <= 45:
        return 5
    return 6


def _parse_questions_json(raw: str, expected: int) -> list[str]:
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON: {raw[:200]}") from exc
    questions = data.get("questions", [])
    if not isinstance(questions, list) or not questions:
        raise ValueError(f"LLM returned invalid structure: {raw[:200]}")
    return [str(q) for q in questions[:expected]]


async def plan_resume_questions(session_id: str, resume_text: str, duration_minutes: int) -> list[Question]:
    """Generate N STAR behavioral questions based on a user's resume via LLM."""
    n = _question_count(duration_minutes)
    prompt = f"""\
Generate exactly {n} distinct behavioral interview questions for a software engineering candidate based on their resume.

Candidate's Resume:
{resume_text}

Requirements:
- Each question must be in STAR style — asking the candidate to describe a specific past experience.
- The questions MUST reference specific projects, roles, or technologies mentioned in the candidate's resume.
- Do NOT use overused openers like "Tell me about yourself" or "What is your greatest weakness".
- Make questions specific, probing, and varied in length and complexity.
- Each question should be a single sentence ending with a period or question mark.

Return ONLY valid JSON with this exact structure (no markdown code fences, no explanation):
{{"questions": ["question 1", "question 2", ...]}}

Generate {n} questions now."""

    raw = await chat_complete(prompt, temperature=0.7)
    question_texts = _parse_questions_json(raw, n)
    return [
        Question(
            session_id=session_id,
            order=i,
            type=QuestionType.behavioral,
            prompt=text,
            follow_up_tree=[],
        )
        for i, text in enumerate(question_texts)
    ]


async def plan_behavioral_questions(session_id: str, duration_minutes: int) -> list[Question]:
    """Generate N STAR behavioral questions via LLM. Raises on failure."""
    n = _question_count(duration_minutes)
    prompt = _BEHAVIORAL_QUESTION_PROMPT.format(n=n)
    raw = await chat_complete(prompt, temperature=0.8)
    question_texts = _parse_questions_json(raw, n)
    return [
        Question(
            session_id=session_id,
            order=i,
            type=QuestionType.behavioral,
            prompt=text,
            follow_up_tree=[],
        )
        for i, text in enumerate(question_texts)
    ]


def _technical_question_count(duration_minutes: int) -> int:
    if duration_minutes <= 30:
        return 1
    if duration_minutes <= 45:
        return 2
    return 3


def plan_questions(
    session_id: str,
    mode: InterviewMode,
    difficulty: Difficulty | None,
    duration_minutes: int,
) -> list[Question]:
    """Pick random problems from problems.json filtered by difficulty."""
    questions: list[Question] = []
    if mode not in (InterviewMode.technical, InterviewMode.mixed):
        return questions

    n = _technical_question_count(duration_minutes)
    all_problems = load_all_problems()
    diff_str = difficulty.value if difficulty else Difficulty.medium.value
    pool = [p for p in all_problems if p.get("difficulty") == diff_str]
    if not pool:
        pool = all_problems

    selected = random.sample(pool, min(n, len(pool)))

    for i, problem in enumerate(selected):
        questions.append(Question(
            session_id=session_id,
            order=i,
            type=QuestionType.technical,
            prompt=problem["prompt"],
            follow_up_tree=[],
            coding_problem_id=problem["id"],
        ))
    return questions
