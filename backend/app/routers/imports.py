from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..import_schemas import ExtractedTextResponse, ImportJobCreate, ImportJobResponse
from ..models import ImportJob, StoredFile, User
from ..security import get_current_active_user
from ..services.import_processing import process_import_job


router = APIRouter(prefix="/imports", tags=["Imports"])


def get_owned_import_job(import_job_id: int, user_id: int, db: Session) -> ImportJob:
    job = db.scalar(
        select(ImportJob).where(
            ImportJob.id == import_job_id,
            ImportJob.user_id == user_id,
        )
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return job


@router.post("", response_model=ImportJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_import_job(
    payload: ImportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stored_file = db.scalar(
        select(StoredFile).where(
            StoredFile.id == payload.file_id,
            StoredFile.user_id == current_user.id,
        )
    )
    if stored_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    job = ImportJob(
        user_id=current_user.id,
        file_id=stored_file.id,
        target_module=payload.target_module,
        status="uploaded",
    )
    stored_file.processing_status = "uploaded"
    stored_file.failure_reason = None
    db.add(job)
    try:
        db.commit()
        db.refresh(job)
    except IntegrityError as error:
        db.rollback()
        existing = db.scalar(
            select(ImportJob).where(
                ImportJob.file_id == stored_file.id,
                ImportJob.target_module == payload.target_module,
            )
        )
        detail = "An import job already exists for this file and module"
        if existing is not None:
            detail += f". Existing import job ID: {existing.id}"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from error

    background_tasks.add_task(process_import_job, job.id)
    return job


@router.get("", response_model=list[ImportJobResponse])
def list_import_jobs(
    target_module: Literal["knowledge", "money", "work"] | None = None,
    import_status: Literal[
        "uploaded", "extracting", "parsing", "awaiting_review", "completed", "failed"
    ] | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(ImportJob).where(ImportJob.user_id == current_user.id)
    if target_module is not None:
        statement = statement.where(ImportJob.target_module == target_module)
    if import_status is not None:
        statement = statement.where(ImportJob.status == import_status)
    statement = statement.order_by(ImportJob.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{import_job_id}", response_model=ImportJobResponse)
def read_import_job(
    import_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_owned_import_job(import_job_id, current_user.id, db)


@router.get("/{import_job_id}/text", response_model=ExtractedTextResponse)
def read_extracted_text(
    import_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = get_owned_import_job(import_job_id, current_user.id, db)
    if job.status not in {"awaiting_review", "completed"} or not job.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Extracted text is not ready",
        )
    return ExtractedTextResponse(
        import_job_id=job.id,
        text=job.extracted_text,
        character_count=len(job.extracted_text),
    )


@router.post("/{import_job_id}/retry", response_model=ImportJobResponse, status_code=status.HTTP_202_ACCEPTED)
def retry_import_job(
    import_job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = get_owned_import_job(import_job_id, current_user.id, db)
    if job.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed import jobs can be retried",
        )
    job.status = "uploaded"
    job.failure_reason = None
    job.started_at = None
    job.completed_at = None
    job.file.processing_status = "uploaded"
    job.file.failure_reason = None
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_import_job, job.id)
    return job
