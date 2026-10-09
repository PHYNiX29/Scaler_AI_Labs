"""Request bodies. Responses are built by each model's to_dict()."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

QuestionType = Literal[
    "welcome", "short_text", "long_text", "multiple_choice", "dropdown", "email",
    "number", "yes_no", "rating", "contact", "date", "thank_you",
]
FormStatus = Literal["draft", "published"]


class FormCreate(BaseModel):
    title: str = Field("My new form", max_length=255)
    description: str = ""
    include_starter: bool = True


class FormUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    theme_settings: Optional[dict] = None


class PublishBody(BaseModel):
    status: Optional[FormStatus] = None  # omitted = toggle


class QuestionCreate(BaseModel):
    question_type: QuestionType
    title: str = Field("", max_length=500)
    description: str = ""
    required: bool = False
    properties: dict = {}
    media: Optional[dict] = None
    logic_jumps: list[dict] = []


class QuestionUpdate(BaseModel):
    question_type: Optional[QuestionType] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    required: Optional[bool] = None
    properties: Optional[dict] = None
    media: Optional[dict] = None
    logic_jumps: Optional[list[dict]] = None


class ReorderBody(BaseModel):
    question_ids: list[str]


class StartBody(BaseModel):
    session_id: Optional[str] = Field(None, max_length=100)


class ValidateStepBody(BaseModel):
    question_id: str
    answer: Any = None


class SubmitBody(BaseModel):
    session_id: Optional[str] = Field(None, max_length=100)
    answers: dict[str, Any] = {}
    time_taken_seconds: int = Field(0, ge=0)
