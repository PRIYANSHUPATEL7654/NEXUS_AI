import csv
import io
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import ImportJob, MoneyImportBatch, MoneyTransaction, MoneyTransactionDraft, StoredFile, User
from ..money_schemas import (
    ManualTransactionCreate, MoneyAnalyticsResponse, MoneyBatchApprovalResponse,
    MoneyBatchApprove, MoneyBatchDetail, MoneyBatchResponse, MoneyDraftResponse,
    MoneyDraftUpdate, MoneyFileImportCreate, MoneyTransactionResponse,
    PastedTransactionImportCreate,
)
from ..security import get_current_active_user
from ..services.file_storage import resolve_storage_path
from ..services.money_duplicates import find_possible_duplicate, transaction_fingerprint
from ..services.money_file_parser import parse_money_file
from ..services.transaction_parser import parse_transaction_text


router = APIRouter(prefix="/money", tags=["Money"])


def owned_batch(batch_id: int, user_id: int, db: Session, with_drafts: bool = False) -> MoneyImportBatch:
    statement = select(MoneyImportBatch).where(MoneyImportBatch.id == batch_id, MoneyImportBatch.user_id == user_id)
    if with_drafts:
        statement = statement.options(selectinload(MoneyImportBatch.drafts))
    batch = db.scalar(statement)
    if batch is None:
        raise HTTPException(status_code=404, detail="Money import batch not found")
    return batch


def owned_draft(draft_id: int, user_id: int, db: Session) -> MoneyTransactionDraft:
    draft = db.scalar(select(MoneyTransactionDraft).where(MoneyTransactionDraft.id == draft_id, MoneyTransactionDraft.user_id == user_id))
    if draft is None:
        raise HTTPException(status_code=404, detail="Transaction draft not found")
    return draft


def batch_detail(batch: MoneyImportBatch, drafts: list[MoneyTransactionDraft]) -> dict:
    return {
        "id": batch.id,
        "user_id": batch.user_id,
        "file_id": batch.file_id,
        "import_job_id": batch.import_job_id,
        "source_type": batch.source_type,
        "status": batch.status,
        "extraction_method": batch.extraction_method,
        "default_currency": batch.default_currency,
        "warnings": batch.warnings,
        "approved_at": batch.approved_at,
        "created_at": batch.created_at,
        "raw_text_retained": batch.raw_text is not None,
        "drafts": drafts,
    }


def duplicate_fields(db: Session, user_id: int, item, seen: set[str]) -> tuple[bool, int | None, list[str]]:
    fingerprint = transaction_fingerprint(item.transaction_date, item.amount, item.transaction_type, item.description)
    warnings = list(item.warnings)
    if fingerprint in seen:
        warnings.append("Possible duplicate inside this import batch")
        return True, None, warnings
    seen.add(fingerprint)
    existing = find_possible_duplicate(
        db, user_id, item.transaction_date, item.amount, item.transaction_type, item.description
    )
    if existing is not None:
        warnings.append(f"Possible duplicate of existing transaction ID {existing.id}")
        return True, existing.id, warnings
    return False, None, warnings


@router.post("/transactions", response_model=MoneyTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_manual_transaction(payload: ManualTransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    values = payload.model_dump()
    transaction = MoneyTransaction(
        user_id=current_user.id,
        source="manual",
        fingerprint=transaction_fingerprint(
            values["transaction_date"], values["amount"], values["transaction_type"], values["description"]
        ),
        **values,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/transactions/export.csv")
def export_transactions_csv(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(MoneyTransaction).where(MoneyTransaction.user_id == current_user.id)
    if date_from:
        statement = statement.where(MoneyTransaction.transaction_date >= date_from)
    if date_to:
        statement = statement.where(MoneyTransaction.transaction_date <= date_to)
    transactions = db.scalars(statement.order_by(MoneyTransaction.transaction_date, MoneyTransaction.id)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "description", "amount", "type", "category", "currency", "source"])
    for item in transactions:
        writer.writerow([
            item.transaction_date.isoformat(), item.description, item.amount,
            item.transaction_type, item.category, item.currency, item.source,
        ])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nexus-money-transactions.csv"},
    )


@router.get("/transactions", response_model=list[MoneyTransactionResponse])
def list_transactions(
    transaction_type: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(MoneyTransaction).where(MoneyTransaction.user_id == current_user.id)
    if transaction_type:
        if transaction_type not in {"expense", "income"}:
            raise HTTPException(status_code=422, detail="Invalid transaction type")
        statement = statement.where(MoneyTransaction.transaction_type == transaction_type)
    if category:
        statement = statement.where(MoneyTransaction.category == category)
    if date_from:
        statement = statement.where(MoneyTransaction.transaction_date >= date_from)
    if date_to:
        statement = statement.where(MoneyTransaction.transaction_date <= date_to)
    return list(db.scalars(statement.order_by(MoneyTransaction.transaction_date.desc(), MoneyTransaction.id.desc()).offset(skip).limit(limit)).all())


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    transaction = db.scalar(select(MoneyTransaction).where(MoneyTransaction.id == transaction_id, MoneyTransaction.user_id == current_user.id))
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(transaction)
    db.commit()
    return Response(status_code=204)


@router.post("/imports/pasted-text", response_model=MoneyBatchDetail, status_code=status.HTTP_201_CREATED)
def import_pasted_text(payload: PastedTransactionImportCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        parsed = parse_transaction_text(payload.text)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    batch = MoneyImportBatch(
        user_id=current_user.id, source_type="pasted_text", status="awaiting_review",
        raw_text=payload.text, extraction_method="local_text_rules_v1",
        default_currency=payload.default_currency, warnings=parsed.warnings,
    )
    db.add(batch)
    db.flush()
    seen: set[str] = set()
    drafts: list[MoneyTransactionDraft] = []
    for index, item in enumerate(parsed.transactions, start=1):
        is_duplicate, duplicate_id, warnings = duplicate_fields(db, current_user.id, item, seen)
        drafts.append(MoneyTransactionDraft(
            user_id=current_user.id, batch_id=batch.id,
            transaction_date=item.transaction_date, description=item.description,
            amount=item.amount, transaction_type=item.transaction_type,
            category=item.category, confidence=item.confidence, warnings=warnings,
            source_location=f"Pasted entry {index}", possible_duplicate=is_duplicate,
            duplicate_transaction_id=duplicate_id,
        ))
    db.add_all(drafts)
    db.commit()
    db.refresh(batch)
    for draft in drafts:
        db.refresh(draft)
    return batch_detail(batch, drafts)


@router.post("/imports/from-job/{import_job_id}", response_model=MoneyBatchDetail, status_code=status.HTTP_201_CREATED)
def import_money_file(
    import_job_id: int,
    payload: MoneyFileImportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = db.scalar(select(ImportJob).where(ImportJob.id == import_job_id, ImportJob.user_id == current_user.id))
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    if job.target_module != "money":
        raise HTTPException(status_code=409, detail="Import job does not target Nexus Money")
    if job.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="File extraction must be awaiting review")
    existing_batch = db.scalar(select(MoneyImportBatch).where(MoneyImportBatch.import_job_id == job.id))
    if existing_batch is not None:
        raise HTTPException(status_code=409, detail=f"Money batch already exists. Batch ID: {existing_batch.id}")
    stored_file = db.scalar(select(StoredFile).where(StoredFile.id == job.file_id, StoredFile.user_id == current_user.id))
    if stored_file is None:
        raise HTTPException(status_code=404, detail="Source file not found")
    try:
        parsed = parse_money_file(resolve_storage_path(stored_file.storage_path), stored_file.extension)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    batch = MoneyImportBatch(
        user_id=current_user.id, file_id=stored_file.id, import_job_id=job.id,
        source_type="file", status="awaiting_review", extraction_method=parsed.extraction_method,
        default_currency=payload.default_currency, warnings=job.warnings + parsed.warnings,
    )
    db.add(batch)
    db.flush()
    seen: set[str] = set()
    drafts: list[MoneyTransactionDraft] = []
    for item in parsed.transactions:
        is_duplicate, duplicate_id, warnings = duplicate_fields(db, current_user.id, item, seen)
        drafts.append(MoneyTransactionDraft(
            user_id=current_user.id, batch_id=batch.id,
            transaction_date=item.transaction_date, description=item.description,
            amount=item.amount, transaction_type=item.transaction_type,
            category=item.category, confidence=item.confidence, warnings=warnings,
            source_location=item.source_location, possible_duplicate=is_duplicate,
            duplicate_transaction_id=duplicate_id,
        ))
    db.add_all(drafts)
    db.commit()
    db.refresh(batch)
    for draft in drafts:
        db.refresh(draft)
    return batch_detail(batch, drafts)


@router.get("/imports", response_model=list[MoneyBatchResponse])
def list_money_imports(batch_status: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    statement = select(MoneyImportBatch).where(MoneyImportBatch.user_id == current_user.id)
    if batch_status:
        if batch_status not in {"awaiting_review", "approved", "cancelled"}:
            raise HTTPException(status_code=422, detail="Invalid batch status")
        statement = statement.where(MoneyImportBatch.status == batch_status)
    return list(db.scalars(statement.order_by(MoneyImportBatch.created_at.desc())).all())


@router.get("/imports/{batch_id}", response_model=MoneyBatchDetail)
def read_money_import(batch_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    batch = owned_batch(batch_id, current_user.id, db, with_drafts=True)
    return batch_detail(batch, list(batch.drafts))


@router.patch("/imports/drafts/{draft_id}", response_model=MoneyDraftResponse)
def update_draft(draft_id: int, payload: MoneyDraftUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    draft = owned_draft(draft_id, current_user.id, db)
    if draft.batch.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review drafts can be changed")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    duplicate = find_possible_duplicate(
        db, current_user.id, draft.transaction_date, draft.amount,
        draft.transaction_type, draft.description,
    )
    draft.possible_duplicate = duplicate is not None
    draft.duplicate_transaction_id = duplicate.id if duplicate else None
    draft.confidence = Decimal("1.000")
    draft.warnings = ([f"Possible duplicate of existing transaction ID {duplicate.id}"] if duplicate else [])
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/imports/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(draft_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    draft = owned_draft(draft_id, current_user.id, db)
    if draft.batch.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review drafts can be deleted")
    db.delete(draft)
    db.commit()
    return Response(status_code=204)


@router.post("/imports/{batch_id}/approve", response_model=MoneyBatchApprovalResponse)
def approve_batch(batch_id: int, payload: MoneyBatchApprove, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    batch = owned_batch(batch_id, current_user.id, db, with_drafts=True)
    if batch.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review batches can be approved")
    if not batch.drafts:
        raise HTTPException(status_code=409, detail="At least one reviewed draft is required")
    duplicate_count = sum(1 for draft in batch.drafts if draft.possible_duplicate)
    if duplicate_count and not payload.confirm_possible_duplicates:
        raise HTTPException(
            status_code=409,
            detail=f"Batch contains {duplicate_count} possible duplicate(s). Delete/correct them or explicitly confirm possible duplicates.",
        )
    transactions = [MoneyTransaction(
        user_id=current_user.id, batch_id=batch.id,
        transaction_date=draft.transaction_date, description=draft.description,
        amount=draft.amount, transaction_type=draft.transaction_type,
        category=draft.category, currency=batch.default_currency, source=batch.source_type,
        fingerprint=transaction_fingerprint(
            draft.transaction_date, draft.amount, draft.transaction_type, draft.description
        ),
    ) for draft in batch.drafts]
    db.add_all(transactions)
    batch.status = "approved"
    batch.approved_at = datetime.now(timezone.utc)
    if payload.delete_raw_text:
        batch.raw_text = None
    if batch.import_job_id:
        job = db.get(ImportJob, batch.import_job_id)
        if job:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            if job.file:
                job.file.processing_status = "completed"
    db.commit()
    return MoneyBatchApprovalResponse(
        batch_id=batch.id, status="approved", transactions_created=len(transactions),
        possible_duplicates_imported=duplicate_count, raw_text_deleted=batch.raw_text is None,
    )


@router.post("/imports/{batch_id}/cancel", response_model=MoneyBatchResponse)
def cancel_batch(batch_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    batch = owned_batch(batch_id, current_user.id, db, with_drafts=True)
    if batch.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only awaiting-review batches can be cancelled")
    for draft in list(batch.drafts):
        db.delete(draft)
    batch.raw_text = None
    batch.status = "cancelled"
    if batch.import_job_id:
        job = db.get(ImportJob, batch.import_job_id)
        if job:
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            if job.file:
                job.file.processing_status = "completed"
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/analytics/summary", response_model=MoneyAnalyticsResponse)
def money_analytics(
    date_from: date | None = None,
    date_to: date | None = None,
    currency: str = Query(default="INR", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    currency = currency.upper()
    statement = select(MoneyTransaction).where(
        MoneyTransaction.user_id == current_user.id,
        MoneyTransaction.currency == currency,
    )
    if date_from:
        statement = statement.where(MoneyTransaction.transaction_date >= date_from)
    if date_to:
        statement = statement.where(MoneyTransaction.transaction_date <= date_to)
    transactions = list(db.scalars(statement.order_by(MoneyTransaction.transaction_date)).all())
    income = sum((item.amount for item in transactions if item.transaction_type == "income"), Decimal("0"))
    expenses = sum((item.amount for item in transactions if item.transaction_type == "expense"), Decimal("0"))
    categories: dict[str, list[Decimal | int]] = defaultdict(lambda: [Decimal("0"), 0])
    months: dict[str, list[Decimal]] = defaultdict(lambda: [Decimal("0"), Decimal("0")])
    for item in transactions:
        if item.transaction_type == "expense":
            categories[item.category][0] += item.amount
            categories[item.category][1] += 1
            months[item.transaction_date.strftime("%Y-%m")][1] += item.amount
        else:
            months[item.transaction_date.strftime("%Y-%m")][0] += item.amount
    category_breakdown = [
        {"category": category, "total": values[0], "transaction_count": values[1]}
        for category, values in sorted(categories.items(), key=lambda pair: pair[1][0], reverse=True)
    ]
    monthly_trend = [
        {"month": month, "income": values[0], "expenses": values[1], "net": values[0] - values[1]}
        for month, values in sorted(months.items())
    ]
    largest = sorted(
        (item for item in transactions if item.transaction_type == "expense"),
        key=lambda item: item.amount,
        reverse=True,
    )[:5]
    return {
        "date_from": date_from, "date_to": date_to, "currency": currency,
        "income_total": income, "expense_total": expenses, "net_total": income - expenses,
        "transaction_count": len(transactions), "category_breakdown": category_breakdown,
        "monthly_trend": monthly_trend, "largest_expenses": largest,
    }
