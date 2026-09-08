from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


TargetModule = Literal["knowledge", "money", "work"]
ImportStatus = Literal[
    "uploaded",
    "extracting",
    "parsing",
    "awaiting_review",
    "completed",
    "failed",
]


class ImportJobCreate(BaseModel):
    file_id: int
    target_module: TargetModule


class ImportJobResponse(BaseModel):
    id: int
    user_id: int
    file_id: int
    target_module: TargetModule
    status: ImportStatus
    extraction_method: str | None
    extracted_item_count: int
    page_count: int | None
    warnings: list[str]
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractedTextResponse(BaseModel):
    import_job_id: int
    text: str
    character_count: int
