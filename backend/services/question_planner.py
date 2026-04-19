"""Generates a starter question plan for a session.

Questions are LLM-generated stubs for now; this will be replaced with
a full prompt-based planner once the AI pipeline is wired in.
"""

from models.interview_session import InterviewMode
from models.question import Question, QuestionType

BEHAVIORAL_PROMPTS = [
    "Tell me about a time you faced a significant technical challenge and how you overcame it.",
    "Describe a situation where you had to collaborate with a difficult teammate.",
    "Give me an example of a project where you had to make a decision with incomplete information.",
    "Tell me about a time you received critical feedback and how you responded.",
]

TECHNICAL_QUESTIONS = [
    {"prompt": "Given an array of integers, find the indices of the two numbers that sum to a target value.", "problem_id": "two-sum"},
    {"prompt": "Given a string of brackets, determine if the input string is valid (brackets close in correct order).", "problem_id": "valid-parentheses"},
    {"prompt": "Given an integer array, find the contiguous subarray which has the largest sum and return its sum.", "problem_id": "maximum-subarray"},
]


def plan_questions(session_id: str, mode: InterviewMode, role: str) -> list[Question]:
    questions: list[Question] = []

    if mode in (InterviewMode.behavioral, InterviewMode.mixed):
        for i, prompt in enumerate(BEHAVIORAL_PROMPTS[:1]):
            questions.append(Question(
                session_id=session_id,
                order=i,
                type=QuestionType.behavioral,
                prompt=prompt,
                follow_up_tree=[],
            ))

    if mode in (InterviewMode.technical, InterviewMode.mixed):
        offset = len(questions)
        for i, q in enumerate(TECHNICAL_QUESTIONS[:1]):
            questions.append(Question(
                session_id=session_id,
                order=offset + i,
                type=QuestionType.technical,
                prompt=q["prompt"],
                follow_up_tree=[],
                coding_problem_id=q["problem_id"],
            ))

    return questions
