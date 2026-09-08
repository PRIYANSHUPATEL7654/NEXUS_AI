from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import ImportJob, StoredFile
from .document_extraction import DocumentExtractionError, extract_document
from .file_storage import resolve_storage_path


def _set_status(
    db: Session,
    job: ImportJob,
    stored_file: StoredFile,
    new_status: str,
) -> None:
    job.status = new_status
    stored_file.processing_status = new_status
    db.commit()


def process_import_job(import_job_id: int) -> None:
    """Run extraction after the API response using a fresh DB session."""
    db = SessionLocal()

    try:
        job = db.get(ImportJob, import_job_id)
        if job is None:
            return

        stored_file = db.get(StoredFile, job.file_id)
        if stored_file is None:
            raise DocumentExtractionError("The source file record no longer exists")

        now = datetime.now(timezone.utc)
        job.started_at = now
        job.completed_at = None
        job.failure_reason = None
        job.warnings = []
        _set_status(db, job, stored_file, "extracting")

        file_path = resolve_storage_path(stored_file.storage_path)
        if not file_path.is_file():
            raise DocumentExtractionError("The stored file content is missing")

        result = extract_document(file_path, stored_file.extension)

        _set_status(db, job, stored_file, "parsing")
        job.extracted_text = result.text
        job.extraction_method = result.extraction_method
        job.extracted_item_count = result.item_count
        job.page_count = result.page_count
        job.warnings = result.warnings
        job.completed_at = datetime.now(timezone.utc)
        _set_status(db, job, stored_file, "awaiting_review")
    except Exception as error:
        db.rollback()
        job = db.get(ImportJob, import_job_id)
        if job is not None:
            job.status = "failed"
            job.failure_reason = str(error)[:2000]
            job.completed_at = datetime.now(timezone.utc)
            stored_file = db.get(StoredFile, job.file_id)
            if stored_file is not None:
                stored_file.processing_status = "failed"
                stored_file.failure_reason = job.failure_reason
            db.commit()
    finally:
        db.close()
