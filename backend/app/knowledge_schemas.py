from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SummaryType = Literal[
    "short",
    "detailed",
    "revision_notes",
    "key_insights",
]


class KnowledgeDocumentCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        cleaned: list[str] = []
        for tag in tags:
            normalized = tag.strip().lower()
            if not normalized:
                continue
            if len(normalized) > 50:
                raise ValueError("Each tag must be 50 characters or fewer")
            if normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned


class KnowledgeDocumentResponse(BaseModel):
    id: int
    user_id: int
    file_id: int | None
    import_job_id: int | None
    title: str
    description: str | None
    tags: list[str]
    extraction_method: str
    page_count: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentDetail(KnowledgeDocumentResponse):
    extracted_text: str


class KnowledgeTextResponse(BaseModel):
    document_id: int
    text: str
    character_count: int


class KnowledgeSummaryCreate(BaseModel):
    summary_type: SummaryType = "detailed"


class KnowledgeSummaryResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    summary_type: SummaryType
    content: str
    generation_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
