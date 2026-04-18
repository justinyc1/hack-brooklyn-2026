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

TECHNICAL_PROMPTS = [
    "Given an array of integers, find the two numbers that sum to a target value.",
    "Implement a function to detect a cycle in a linked list.",
    "Design a data structure that supports insert, delete, and getRandom in O(1).",
]


def plan_questions(session_id: str, mode: InterviewMode, role: str) -> list[Question]:
    questions: list[Question] = []

    if mode in (InterviewMode.behavioral, InterviewMode.mixed):
        for i, prompt in enumerate(BEHAVIORAL_PROMPTS[:3]):
            questions.append(Question(
                session_id=session_id,
                order=i,
                type=QuestionType.behavioral,
                prompt=prompt,
                follow_up_tree=[],
            ))

    if mode in (InterviewMode.technical, InterviewMode.mixed):
        offset = len(questions)
        for i, prompt in enumerate(TECHNICAL_PROMPTS[:2]):
            questions.append(Question(
                session_id=session_id,
                order=offset + i,
                type=QuestionType.technical,
                prompt=prompt,
                follow_up_tree=[],
            ))

    return questions
