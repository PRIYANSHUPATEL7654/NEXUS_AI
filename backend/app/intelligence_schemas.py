from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IntelligenceToolDescriptor(BaseModel):
    name: str
    description: str
    read_only: bool = True
    required_parameters: list[str] = Field(default_factory=list)
    optional_parameters: list[str] = Field(default_factory=list)


class IntelligenceSearchResult(BaseModel):
    module: Literal["knowledge", "learn", "money", "work"]
    record_type: str
    record_id: int
    title: str
    snippet: str
    score: int
    route: str


class IntelligenceSearchResponse(BaseModel):
    query: str
    total: int
    results: list[IntelligenceSearchResult]


class DailyBriefSection(BaseModel):
    title: str
    value: str
    detail: str
    severity: Literal["info", "success", "warning", "urgent"] = "info"
    route: str | None = None


class DailyBriefResponse(BaseModel):
    local_date: date
    timezone: str
    greeting: str
    summary: str
    sections: list[DailyBriefSection]


class IntelligenceRecommendation(BaseModel):
    module: Literal["knowledge", "learn", "money", "work"]
    priority: int = Field(ge=1, le=5)
    title: str
    reason: str
    evidence: list[str]
    action: str
    route: str


class IntelligenceRecommendationsResponse(BaseModel):
    generated_for: date
    recommendations: list[IntelligenceRecommendation]


class IntelligenceToolRunRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class IntelligenceToolRunResponse(BaseModel):
    run_id: int
    tool_name: str
    status: Literal["completed"]
    result: dict[str, Any]


class AskNexusRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


class AskNexusResponse(BaseModel):
    run_id: int
    intent: str
    answer: str
    tools_used: list[str]
    data: dict[str, Any]


class IntelligenceRunResponse(BaseModel):
    id: int
    user_id: int
    operation: str
    tool_name: str | None
    status: Literal["completed", "failed"]
    request_payload: dict[str, Any]
    result_summary: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
