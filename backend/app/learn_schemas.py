from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


GoalStatus = Literal["active", "paused", "completed"]
TopicStatus = Literal["not_started", "in_progress", "mastered"]


class LearningGoalCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    target_date: date | None = None
    priority: int = Field(default=3, ge=1, le=5)


class LearningGoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    target_date: date | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    status: GoalStatus | None = None

    @model_validator(mode="after")
    def reject_empty_update(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        return self


class LearningGoalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    target_date: date | None
    status: GoalStatus
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningTopicCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    source_document_id: int | None = Field(default=None, ge=1)
    current_level: int = Field(default=0, ge=0, le=100)
    target_level: int = Field(default=80, ge=1, le=100)


class LearningTopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    source_document_id: int | None = Field(default=None, ge=1)
    target_level: int | None = Field(default=None, ge=1, le=100)
    status: TopicStatus | None = None

    @model_validator(mode="after")
    def reject_empty_update(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        return self


class LearningTopicResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    source_document_id: int | None
    title: str
    description: str | None
    current_level: int
    target_level: int
    status: TopicStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningProgressCreate(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    study_minutes: int = Field(default=0, ge=0, le=1440)
    notes: str | None = Field(default=None, max_length=2000)


class LearningProgressResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    progress_percent: int
    study_minutes: int
    notes: str | None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillGapResponse(BaseModel):
    topic_id: int
    topic_title: str
    current_level: int
    target_level: int
    gap: int
    recommended_action: str


class QuizGenerateRequest(BaseModel):
    question_count: int = Field(default=5, ge=1, le=10)


class QuizQuestionResponse(BaseModel):
    id: int
    topic_id: int
    question: str
    options: list[str]
    generation_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizAnswerCreate(BaseModel):
    selected_option_index: int = Field(ge=0, le=3)


class QuizAnswerResponse(BaseModel):
    attempt_id: int
    question_id: int
    selected_option_index: int
    correct_option_index: int
    is_correct: bool
    explanation: str
    attempted_at: datetime


class QuizScoreResponse(BaseModel):
    topic_id: int
    attempts: int
    correct_answers: int
    score_percent: float


class QuizReadyDocumentResponse(BaseModel):
    document_id: int
    title: str
    character_count: int
    sentence_count: int
    keyword_count: int
    quiz_ready: bool
    reason: str


class TopicQuizReadinessResponse(QuizReadyDocumentResponse):
    topic_id: int
    topic_title: str
