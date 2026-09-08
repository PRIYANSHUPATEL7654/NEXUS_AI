from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ProjectStatus = Literal["planned", "in_progress", "blocked", "completed", "cancelled"]
TaskStatus = Literal["backlog", "planned", "in_progress", "blocked", "completed", "cancelled"]


class WorkProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    client_name: str | None = Field(default=None, max_length=200)
    status: ProjectStatus = "planned"
    due_date: date | None = None


class WorkProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    client_name: str | None = Field(default=None, max_length=200)
    status: ProjectStatus | None = None
    due_date: date | None = None

    @model_validator(mode="after")
    def reject_empty(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one project field")
        return self


class WorkProjectResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    client_name: str | None
    status: ProjectStatus
    due_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkTaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    description: str | None = Field(default=None, max_length=5000)
    parent_task_id: int | None = None
    status: TaskStatus = "planned"
    priority: int = Field(default=3, ge=1, le=5)
    complexity: int = Field(default=3, ge=1, le=5)
    due_date: date | None = None
    estimated_minutes_low: int = Field(gt=0, le=100_000)
    estimated_minutes_high: int = Field(gt=0, le=100_000)
    dependencies: list[int] = Field(default_factory=list, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_range(self):
        if self.estimated_minutes_high < self.estimated_minutes_low:
            raise ValueError("estimated_minutes_high must be at least estimated_minutes_low")
        return self


class WorkTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    complexity: int | None = Field(default=None, ge=1, le=5)
    due_date: date | None = None
    estimated_minutes_low: int | None = Field(default=None, gt=0, le=100_000)
    estimated_minutes_high: int | None = Field(default=None, gt=0, le=100_000)
    actual_minutes: int | None = Field(default=None, ge=0, le=100_000)
    dependencies: list[int] | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def reject_empty(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one task field")
        if self.estimated_minutes_low is not None and self.estimated_minutes_high is not None:
            if self.estimated_minutes_high < self.estimated_minutes_low:
                raise ValueError("estimated_minutes_high must be at least estimated_minutes_low")
        return self


class WorkTaskResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    parent_task_id: int | None
    source_plan_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    priority: int
    complexity: int
    due_date: date | None
    estimated_minutes_low: int
    estimated_minutes_high: int
    actual_minutes: int | None
    dependencies: list[int]
    notes: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkTaskDraftResponse(BaseModel):
    id: int
    user_id: int
    plan_import_id: int
    title: str
    description: str | None
    priority: int
    complexity: int
    due_date: date | None
    estimated_minutes_low: int
    estimated_minutes_high: int
    confidence: Decimal
    source_location: str | None
    warnings: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkTaskDraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    description: str | None = Field(default=None, max_length=5000)
    priority: int | None = Field(default=None, ge=1, le=5)
    complexity: int | None = Field(default=None, ge=1, le=5)
    due_date: date | None = None
    estimated_minutes_low: int | None = Field(default=None, gt=0, le=100_000)
    estimated_minutes_high: int | None = Field(default=None, gt=0, le=100_000)

    @model_validator(mode="after")
    def reject_empty(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one draft field")
        return self


class WorkPlanImportCreate(BaseModel):
    project_id: int | None = None
    fallback_project_title: str = Field(default="Imported work plan", min_length=2, max_length=200)


class WorkPlanImportResponse(BaseModel):
    id: int
    user_id: int
    project_id: int | None
    file_id: int | None
    import_job_id: int | None
    status: Literal["awaiting_review", "approved", "cancelled"]
    proposed_project_title: str
    extraction_method: str | None
    estimated_minutes_low: int
    estimated_minutes_high: int
    estimate_confidence: Literal["low", "medium", "high"]
    assumptions: list[str]
    warnings: list[str]
    approved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkPlanImportDetail(WorkPlanImportResponse):
    drafts: list[WorkTaskDraftResponse]


class WorkPlanApprove(BaseModel):
    create_project_if_missing: bool = True


class WorkPlanApprovalResponse(BaseModel):
    plan_import_id: int
    status: Literal["approved"]
    project_id: int
    tasks_created: int
    estimated_minutes_low: int
    estimated_minutes_high: int


class WorkProjectEstimateResponse(BaseModel):
    project_id: int
    pending_task_count: int
    estimated_minutes_low: int
    estimated_minutes_high: int
    completed_actual_minutes: int
    assumptions: list[str]


class WorkDashboardResponse(BaseModel):
    total_projects: int
    active_projects: int
    pending_tasks: int
    blocked_tasks: int
    completed_tasks: int
    overdue_tasks: int
    estimated_remaining_minutes_low: int
    estimated_remaining_minutes_high: int
