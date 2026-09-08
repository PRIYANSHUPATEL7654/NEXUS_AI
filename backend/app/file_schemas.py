from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


FileProcessingStatus = Literal[
    "uploaded",
    "extracting",
    "parsing",
    "awaiting_review",
    "completed",
    "failed",
]


class StoredFileResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    content_type: str
    extension: str
    size_bytes: int
    sha256_hash: str
    processing_status: FileProcessingStatus
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
