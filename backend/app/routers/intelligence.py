from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..intelligence_schemas import (
    AskNexusRequest, AskNexusResponse, DailyBriefResponse,
    IntelligenceRecommendationsResponse, IntelligenceRunResponse,
    IntelligenceSearchResponse, IntelligenceToolDescriptor,
    IntelligenceToolRunRequest, IntelligenceToolRunResponse,
)
from ..models import IntelligenceRun, User
from ..security import get_current_active_user
from ..services.intelligence import (
    TOOL_REGISTRY, ask_nexus, cross_module_search, daily_brief,
    recommendations, run_tool,
)


router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


def save_run(
    db: Session,
    user_id: int,
    operation: str,
    tool_name: str | None,
    run_status: str,
    request_summary: dict[str, Any],
    result_summary: dict[str, Any],
) -> IntelligenceRun:
    run = IntelligenceRun(
        user_id=user_id, operation=operation, tool_name=tool_name,
        status=run_status, request_payload=jsonable_encoder(request_summary),
        result_summary=jsonable_encoder(result_summary),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/tools", response_model=list[IntelligenceToolDescriptor])
def list_tools(current_user: User = Depends(get_current_active_user)):
    del current_user
    return [
        {
            "name": name, "description": details["description"], "read_only": True,
            "required_parameters": details["required_parameters"],
            "optional_parameters": details["optional_parameters"],
        }
        for name, details in TOOL_REGISTRY.items()
    ]


@router.get("/search", response_model=IntelligenceSearchResponse)
def search_nexus(
    q: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = cross_module_search(db, current_user.id, q, limit)
    save_run(db, current_user.id, "search", "cross_module_search", "completed", {"query_length": len(q), "limit": limit}, {"result_count": result["total"]})
    return result


@router.get("/daily-brief", response_model=DailyBriefResponse)
def get_daily_brief(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    result = daily_brief(db, current_user)
    save_run(db, current_user.id, "daily_brief", "daily_brief", "completed", {}, {"section_count": len(result["sections"]), "local_date": result["local_date"]})
    return result


@router.get("/recommendations", response_model=IntelligenceRecommendationsResponse)
def get_recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    result = recommendations(db, current_user)
    save_run(db, current_user.id, "recommendations", "recommendations", "completed", {}, {"recommendation_count": len(result["recommendations"])})
    return result


@router.post("/tools/{tool_name}/run", response_model=IntelligenceToolRunResponse)
def execute_tool(
    tool_name: str,
    payload: IntelligenceToolRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        result = run_tool(db, current_user, tool_name, payload.parameters)
    except LookupError as error:
        save_run(db, current_user.id, "tool", tool_name, "failed", {"parameter_keys": sorted(payload.parameters)}, {"error": str(error)})
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (KeyError, TypeError, ValueError) as error:
        message = str(error).strip("'")
        save_run(db, current_user.id, "tool", tool_name, "failed", {"parameter_keys": sorted(payload.parameters)}, {"error": message})
        raise HTTPException(status_code=422, detail=message) from error
    run = save_run(db, current_user.id, "tool", tool_name, "completed", {"parameter_keys": sorted(payload.parameters)}, {"result_keys": sorted(result)})
    return {"run_id": run.id, "tool_name": tool_name, "status": "completed", "result": jsonable_encoder(result)}


@router.post("/ask", response_model=AskNexusResponse)
def ask(
    payload: AskNexusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        intent, answer, tools_used, data = ask_nexus(db, current_user, payload.message)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    run = save_run(
        db, current_user.id, "ask", tools_used[0] if tools_used else None, "completed",
        {"message_length": len(payload.message)}, {"intent": intent, "tools_used": tools_used},
    )
    return {
        "run_id": run.id, "intent": intent, "answer": answer,
        "tools_used": tools_used, "data": jsonable_encoder(data),
    }


@router.get("/runs", response_model=list[IntelligenceRunResponse])
def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list(db.scalars(
        select(IntelligenceRun).where(IntelligenceRun.user_id == current_user.id).order_by(IntelligenceRun.created_at.desc()).limit(limit)
    ).all())
