from enum import Enum
from pydantic import Field
from models.base import MongoBase


class QuestionType(str, Enum):
    behavioral = "behavioral"
    technical = "technical"
    follow_up = "follow_up"


class FollowUpBranch(MongoBase):
    trigger: str
    prompt: str
    follow_ups: list["FollowUpBranch"] = Field(default_factory=list)


FollowUpBranch.model_rebuild()


class Question(MongoBase):
    session_id: str
    order: int
    type: QuestionType
    prompt: str
    follow_up_tree: list[FollowUpBranch] = Field(default_factory=list)
    coding_problem_id: str | None = None
