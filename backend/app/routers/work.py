from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import ImportJob, User, WorkPlanImport, WorkProject, WorkTask, WorkTaskDraft
from ..security import get_current_active_user
from ..services.work_plan_parser import parse_work_plan
from ..work_schemas import (
    WorkDashboardResponse, WorkPlanApprovalResponse, WorkPlanApprove,
    WorkPlanImportCreate, WorkPlanImportDetail, WorkPlanImportResponse,
    WorkProjectCreate, WorkProjectEstimateResponse, WorkProjectResponse,
    WorkProjectUpdate, WorkTaskCreate, WorkTaskDraftResponse,
    WorkTaskDraftUpdate, WorkTaskResponse, WorkTaskUpdate,
)


router = APIRouter(prefix="/work", tags=["Work"])


def owned_project(project_id: int, user_id: int, db: Session) -> WorkProject:
    project = db.scalar(select(WorkProject).where(WorkProject.id == project_id, WorkProject.user_id == user_id))
    if project is None:
        raise HTTPException(status_code=404, detail="Work project not found")
    return project


def owned_task(task_id: int, user_id: int, db: Session) -> WorkTask:
    task = db.scalar(select(WorkTask).where(WorkTask.id == task_id, WorkTask.user_id == user_id))
    if task is None:
        raise HTTPException(status_code=404, detail="Work task not found")
    return task


def owned_plan(plan_id: int, user_id: int, db: Session, with_drafts: bool = False) -> WorkPlanImport:
    statement = select(WorkPlanImport).where(WorkPlanImport.id == plan_id, WorkPlanImport.user_id == user_id)
    if with_drafts:
        statement = statement.options(selectinload(WorkPlanImport.drafts))
    plan = db.scalar(statement)
    if plan is None:
        raise HTTPException(status_code=404, detail="Work plan import not found")
    return plan


@router.post("/projects", response_model=WorkProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: WorkProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = WorkProject(user_id=current_user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[WorkProjectResponse])
def list_projects(
    project_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(WorkProject).where(WorkProject.user_id == current_user.id)
    if project_status:
        allowed = {"planned", "in_progress", "blocked", "completed", "cancelled"}
        if project_status not in allowed:
            raise HTTPException(status_code=422, detail="Invalid project status")
        statement = statement.where(WorkProject.status == project_status)
    return list(db.scalars(statement.order_by(WorkProject.created_at.desc())).all())


@router.get("/projects/{project_id}", response_model=WorkProjectResponse)
def read_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return owned_project(project_id, current_user.id, db)


@router.patch("/projects/{project_id}", response_model=WorkProjectResponse)
def update_project(project_id: int, payload: WorkProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    project = owned_project(project_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.post("/projects/{project_id}/tasks", response_model=WorkTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, payload: WorkTaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_project(project_id, current_user.id, db)
    if payload.parent_task_id is not None:
        parent = owned_task(payload.parent_task_id, current_user.id, db)
        if parent.project_id != project_id:
            raise HTTPException(status_code=409, detail="Parent task must belong to the same project")
    for dependency_id in payload.dependencies:
        dependency = owned_task(dependency_id, current_user.id, db)
        if dependency.project_id != project_id:
            raise HTTPException(status_code=409, detail="Dependencies must belong to the same project")
    task = WorkTask(user_id=current_user.id, project_id=project_id, **payload.model_dump())
    if task.status == "completed":
        task.completed_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[WorkTaskResponse])
def list_tasks(
    project_id: int | None = None,
    task_status: str | None = Query(default=None, alias="status"),
    due_before: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(WorkTask).where(WorkTask.user_id == current_user.id)
    if project_id is not None:
        owned_project(project_id, current_user.id, db)
        statement = statement.where(WorkTask.project_id == project_id)
    if task_status:
        allowed = {"backlog", "planned", "in_progress", "blocked", "completed", "cancelled"}
        if task_status not in allowed:
            raise HTTPException(status_code=422, detail="Invalid task status")
        statement = statement.where(WorkTask.status == task_status)
    if due_before:
        statement = statement.where(WorkTask.due_date <= due_before)
    return list(db.scalars(statement.order_by(WorkTask.due_date.asc().nullslast(), WorkTask.priority.desc())).all())


@router.patch("/tasks/{task_id}", response_model=WorkTaskResponse)
def update_task(task_id: int, payload: WorkTaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    task = owned_task(task_id, current_user.id, db)
    values = payload.model_dump(exclude_unset=True)
    low = values.get("estimated_minutes_low", task.estimated_minutes_low)
    high = values.get("estimated_minutes_high", task.estimated_minutes_high)
    if high < low:
        raise HTTPException(status_code=422, detail="estimated_minutes_high must be at least estimated_minutes_low")
    if "dependencies" in values:
        for dependency_id in values["dependencies"]:
            if dependency_id == task.id:
                raise HTTPException(status_code=422, detail="A task cannot depend on itself")
            dependency = owned_task(dependency_id, current_user.id, db)
            if dependency.project_id != task.project_id:
                raise HTTPException(status_code=409, detail="Dependencies must belong to the same project")
    for field, value in values.items():
        setattr(task, field, value)
    if "status" in values:
        task.completed_at = datetime.now(timezone.utc) if task.status == "completed" else None
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    task = owned_task(task_id, current_user.id, db)
    db.delete(task)
    db.commit()
    return Response(status_code=204)


@router.post("/imports/from-job/{import_job_id}", response_model=WorkPlanImportDetail, status_code=status.HTTP_201_CREATED)
def create_work_plan_from_job(
    import_job_id: int,
    payload: WorkPlanImportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = db.scalar(select(ImportJob).where(ImportJob.id == import_job_id, ImportJob.user_id == current_user.id))
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    if job.target_module != "work":
        raise HTTPException(status_code=409, detail="Import job does not target Nexus Work")
    if job.status != "awaiting_review" or not job.extracted_text:
        raise HTTPException(status_code=409, detail="Extracted work text must be awaiting review")
    existing = db.scalar(select(WorkPlanImport).where(WorkPlanImport.import_job_id == job.id))
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Work plan already exists. Plan ID: {existing.id}")
    if payload.project_id is not None:
        owned_project(payload.project_id, current_user.id, db)
    try:
        parsed = parse_work_plan(job.extracted_text, payload.fallback_project_title)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    plan = WorkPlanImport(
        user_id=current_user.id, project_id=payload.project_id,
        file_id=job.file_id, import_job_id=job.id, status="awaiting_review",
        proposed_project_title=parsed.project_title,
        extraction_method=f"{job.extraction_method}+local_work_rules_v1",
        estimated_minutes_low=parsed.estimated_minutes_low,
        estimated_minutes_high=parsed.estimated_minutes_high,
        estimate_confidence=parsed.estimate_confidence,
        assumptions=parsed.assumptions, warnings=job.warnings + parsed.warnings,
    )
    db.add(plan)
    db.flush()
    drafts = [WorkTaskDraft(
        user_id=current_user.id, plan_import_id=plan.id,
        title=item.title, description=item.description, priority=item.priority,
        complexity=item.complexity, due_date=item.due_date,
        estimated_minutes_low=item.estimated_minutes_low,
        estimated_minutes_high=item.estimated_minutes_high,
        confidence=item.confidence, source_location=item.source_location,
        warnings=item.warnings,
    ) for item in parsed.tasks]
    db.add_all(drafts)
    db.commit()
    db.refresh(plan)
    for draft in drafts:
        db.refresh(draft)
    return {**WorkPlanImportResponse.model_validate(plan).model_dump(), "drafts": drafts}


@router.get("/imports", response_model=list[WorkPlanImportResponse])
def list_work_plan_imports(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return list(db.scalars(
        select(WorkPlanImport).where(WorkPlanImport.user_id == current_user.id).order_by(WorkPlanImport.created_at.desc())
    ).all())


@router.get("/imports/{plan_id}", response_model=WorkPlanImportDetail)
def read_work_plan_import(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    plan = owned_plan(plan_id, current_user.id, db, with_drafts=True)
    return {**WorkPlanImportResponse.model_validate(plan).model_dump(), "drafts": plan.drafts}


@router.patch("/imports/drafts/{draft_id}", response_model=WorkTaskDraftResponse)
def update_work_draft(draft_id: int, payload: WorkTaskDraftUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    draft = db.scalar(select(WorkTaskDraft).where(WorkTaskDraft.id == draft_id, WorkTaskDraft.user_id == current_user.id))
    if draft is None:
        raise HTTPException(status_code=404, detail="Work task draft not found")
    if draft.plan_import.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review work drafts can be changed")
    values = payload.model_dump(exclude_unset=True)
    low = values.get("estimated_minutes_low", draft.estimated_minutes_low)
    high = values.get("estimated_minutes_high", draft.estimated_minutes_high)
    if high < low:
        raise HTTPException(status_code=422, detail="estimated_minutes_high must be at least estimated_minutes_low")
    for field, value in values.items():
        setattr(draft, field, value)
    draft.confidence = Decimal("1.000")
    draft.warnings = []
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/imports/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_draft(draft_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    draft = db.scalar(select(WorkTaskDraft).where(WorkTaskDraft.id == draft_id, WorkTaskDraft.user_id == current_user.id))
    if draft is None:
        raise HTTPException(status_code=404, detail="Work task draft not found")
    if draft.plan_import.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review work drafts can be deleted")
    db.delete(draft)
    db.commit()
    return Response(status_code=204)


@router.post("/imports/{plan_id}/approve", response_model=WorkPlanApprovalResponse)
def approve_work_plan(plan_id: int, payload: WorkPlanApprove, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    plan = owned_plan(plan_id, current_user.id, db, with_drafts=True)
    if plan.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review work plans can be approved")
    if not plan.drafts:
        raise HTTPException(status_code=409, detail="At least one reviewed task draft is required")
    project = plan.project
    if project is None:
        if not payload.create_project_if_missing:
            raise HTTPException(status_code=409, detail="Select a project or allow project creation")
        project = WorkProject(
            user_id=current_user.id, title=plan.proposed_project_title,
            description="Created from an approved work document", status="planned",
        )
        db.add(project)
        db.flush()
        plan.project_id = project.id
    tasks = [WorkTask(
        user_id=current_user.id, project_id=project.id, source_plan_id=plan.id,
        title=draft.title, description=draft.description, status="planned",
        priority=draft.priority, complexity=draft.complexity, due_date=draft.due_date,
        estimated_minutes_low=draft.estimated_minutes_low,
        estimated_minutes_high=draft.estimated_minutes_high,
        dependencies=[],
    ) for draft in plan.drafts]
    db.add_all(tasks)
    plan.status = "approved"
    plan.approved_at = datetime.now(timezone.utc)
    job = db.get(ImportJob, plan.import_job_id) if plan.import_job_id else None
    if job:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        if job.file:
            job.file.processing_status = "completed"
    db.commit()
    return WorkPlanApprovalResponse(
        plan_import_id=plan.id, status="approved", project_id=project.id,
        tasks_created=len(tasks), estimated_minutes_low=sum(task.estimated_minutes_low for task in tasks),
        estimated_minutes_high=sum(task.estimated_minutes_high for task in tasks),
    )


@router.post("/imports/{plan_id}/cancel", response_model=WorkPlanImportResponse)
def cancel_work_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    plan = owned_plan(plan_id, current_user.id, db, with_drafts=True)
    if plan.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review work plans can be cancelled")
    for draft in list(plan.drafts):
        db.delete(draft)
    plan.status = "cancelled"
    job = db.get(ImportJob, plan.import_job_id) if plan.import_job_id else None
    if job:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        if job.file:
            job.file.processing_status = "completed"
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/projects/{project_id}/estimate", response_model=WorkProjectEstimateResponse)
def project_estimate(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    owned_project(project_id, current_user.id, db)
    tasks = list(db.scalars(select(WorkTask).where(WorkTask.project_id == project_id, WorkTask.user_id == current_user.id)).all())
    pending = [task for task in tasks if task.status not in {"completed", "cancelled"}]
    completed_actual = sum(task.actual_minutes or 0 for task in tasks if task.status == "completed")
    return {
        "project_id": project_id, "pending_task_count": len(pending),
        "estimated_minutes_low": sum(task.estimated_minutes_low for task in pending),
        "estimated_minutes_high": sum(task.estimated_minutes_high for task in pending),
        "completed_actual_minutes": completed_actual,
        "assumptions": [
            "Pending estimates are added without parallel-work reduction",
            "Blocked/external waiting time is not included",
            "Actual minutes improve future learned estimation after enough history exists",
        ],
    }


@router.get("/dashboard", response_model=WorkDashboardResponse)
def work_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    projects = list(db.scalars(select(WorkProject).where(WorkProject.user_id == current_user.id)).all())
    tasks = list(db.scalars(select(WorkTask).where(WorkTask.user_id == current_user.id)).all())
    today = date.today()
    pending = [task for task in tasks if task.status not in {"completed", "cancelled"}]
    return {
        "total_projects": len(projects),
        "active_projects": sum(project.status in {"planned", "in_progress", "blocked"} for project in projects),
        "pending_tasks": len(pending),
        "blocked_tasks": sum(task.status == "blocked" for task in tasks),
        "completed_tasks": sum(task.status == "completed" for task in tasks),
        "overdue_tasks": sum(task.due_date is not None and task.due_date < today for task in pending),
        "estimated_remaining_minutes_low": sum(task.estimated_minutes_low for task in pending),
        "estimated_remaining_minutes_high": sum(task.estimated_minutes_high for task in pending),
    }
