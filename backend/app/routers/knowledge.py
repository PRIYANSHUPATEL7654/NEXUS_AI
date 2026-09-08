import re
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..knowledge_schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentDetail,
    KnowledgeDocumentResponse,
    KnowledgeSummaryCreate,
    KnowledgeSummaryResponse,
    KnowledgeTextResponse,
)
from ..models import ImportJob, KnowledgeDocument, KnowledgeSummary, User
from ..security import get_current_active_user
from ..services.pdf_export import create_summary_pdf
from ..services.summarization import SummarizationError, summarize_text


router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


def get_owned_document(document_id: int, user_id: int, db: Session) -> KnowledgeDocument:
    document = db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.user_id == user_id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    return document


def get_owned_summary(summary_id: int, user_id: int, db: Session) -> KnowledgeSummary:
    summary = db.scalar(
        select(KnowledgeSummary).where(
            KnowledgeSummary.id == summary_id,
            KnowledgeSummary.user_id == user_id,
        )
    )
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge summary not found")
    return summary


@router.post(
    "/documents/from-import/{import_job_id}",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_from_import(
    import_job_id: int,
    payload: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = db.scalar(
        select(ImportJob).where(
            ImportJob.id == import_job_id,
            ImportJob.user_id == current_user.id,
        )
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    if job.target_module != "knowledge":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This import job does not target Nexus Knowledge",
        )
    if job.status != "awaiting_review" or not job.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The import must reach awaiting_review before it can become a Knowledge document",
        )

    default_title = Path(job.file.original_filename).stem.replace("_", " ").strip()
    document = KnowledgeDocument(
        user_id=current_user.id,
        file_id=job.file_id,
        import_job_id=job.id,
        title=payload.title or default_title or "Untitled document",
        description=payload.description,
        tags=payload.tags,
        extracted_text=job.extracted_text,
        extraction_method=job.extraction_method or "unknown",
        page_count=job.page_count,
    )
    db.add(document)
    job.status = "completed"
    job.file.processing_status = "completed"
    job.file.failure_reason = None

    try:
        db.commit()
        db.refresh(document)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This import has already been added to Nexus Knowledge",
        ) from error
    return document


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
def list_documents(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(KnowledgeDocument).where(
        KnowledgeDocument.user_id == current_user.id
    )
    if search:
        statement = statement.where(KnowledgeDocument.title.ilike(f"%{search}%"))
    statement = statement.order_by(KnowledgeDocument.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentDetail)
def read_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_owned_document(document_id, current_user.id, db)


@router.get("/documents/{document_id}/text", response_model=KnowledgeTextResponse)
def read_document_text(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    document = get_owned_document(document_id, current_user.id, db)
    return KnowledgeTextResponse(
        document_id=document.id,
        text=document.extracted_text,
        character_count=len(document.extracted_text),
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    document = get_owned_document(document_id, current_user.id, db)
    if document.import_job is not None:
        document.import_job.status = "awaiting_review"
        document.import_job.file.processing_status = "awaiting_review"
    db.delete(document)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/documents/{document_id}/summaries",
    response_model=KnowledgeSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_summary(
    document_id: int,
    payload: KnowledgeSummaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    document = get_owned_document(document_id, current_user.id, db)
    try:
        content = summarize_text(document.extracted_text, payload.summary_type)
    except SummarizationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    summary = KnowledgeSummary(
        user_id=current_user.id,
        document_id=document.id,
        summary_type=payload.summary_type,
        content=content,
        generation_method="local_extractive_v1",
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


@router.get(
    "/documents/{document_id}/summaries",
    response_model=list[KnowledgeSummaryResponse],
)
def list_document_summaries(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    document = get_owned_document(document_id, current_user.id, db)
    statement = (
        select(KnowledgeSummary)
        .where(
            KnowledgeSummary.document_id == document.id,
            KnowledgeSummary.user_id == current_user.id,
        )
        .order_by(KnowledgeSummary.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.get("/summaries/{summary_id}", response_model=KnowledgeSummaryResponse)
def read_summary(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_owned_summary(summary_id, current_user.id, db)


@router.get("/summaries/{summary_id}/pdf")
def download_summary_pdf(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    summary = get_owned_summary(summary_id, current_user.id, db)
    pdf_bytes = create_summary_pdf(
        document_title=summary.document.title,
        summary_type=summary.summary_type,
        summary_content=summary.content,
        timezone_name=(
            current_user.profile.timezone
            if current_user.profile is not None
            else "UTC"
        ),
    )
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", summary.document.title).strip("-")
    filename = f"{safe_stem or 'knowledge'}-{summary.summary_type}-summary.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
