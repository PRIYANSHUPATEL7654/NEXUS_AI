from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TransactionType = Literal["expense", "income"]
MoneyCategory = Literal[
    "Food", "Transport", "Shopping", "Bills", "Health", "Education",
    "Entertainment", "Housing", "Salary", "Transfer", "Other",
]


class ManualTransactionCreate(BaseModel):
    transaction_date: date
    description: str = Field(min_length=2, max_length=500)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    transaction_type: TransactionType
    category: MoneyCategory
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class MoneyTransactionResponse(BaseModel):
    id: int
    user_id: int
    batch_id: int | None
    transaction_date: date
    description: str
    amount: Decimal
    transaction_type: TransactionType
    category: MoneyCategory
    currency: str
    source: Literal["manual", "pasted_text", "file"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PastedTransactionImportCreate(BaseModel):
    text: str = Field(min_length=3, max_length=50_000)
    default_currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("default_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class MoneyFileImportCreate(BaseModel):
    default_currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("default_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class MoneyDraftResponse(BaseModel):
    id: int
    user_id: int
    batch_id: int
    transaction_date: date
    description: str
    amount: Decimal
    transaction_type: TransactionType
    category: MoneyCategory
    confidence: Decimal
    warnings: list[str]
    source_location: str | None
    possible_duplicate: bool
    duplicate_transaction_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MoneyDraftUpdate(BaseModel):
    transaction_date: date | None = None
    description: str | None = Field(default=None, min_length=2, max_length=500)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    transaction_type: TransactionType | None = None
    category: MoneyCategory | None = None

    @model_validator(mode="after")
    def reject_empty_update(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one draft field to update")
        return self


class MoneyBatchResponse(BaseModel):
    id: int
    user_id: int
    file_id: int | None
    import_job_id: int | None
    source_type: Literal["pasted_text", "file"]
    status: Literal["awaiting_review", "approved", "cancelled"]
    extraction_method: str | None
    default_currency: str
    warnings: list[str]
    approved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MoneyBatchDetail(MoneyBatchResponse):
    raw_text_retained: bool
    drafts: list[MoneyDraftResponse]


class MoneyBatchApprove(BaseModel):
    delete_raw_text: bool = True
    confirm_possible_duplicates: bool = False


class MoneyBatchApprovalResponse(BaseModel):
    batch_id: int
    status: Literal["approved"]
    transactions_created: int
    possible_duplicates_imported: int
    raw_text_deleted: bool


class MoneyCategoryTotal(BaseModel):
    category: str
    total: Decimal
    transaction_count: int


class MoneyMonthlyTotal(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal


class MoneyAnalyticsResponse(BaseModel):
    date_from: date | None
    date_to: date | None
    currency: str
    income_total: Decimal
    expense_total: Decimal
    net_total: Decimal
    transaction_count: int
    category_breakdown: list[MoneyCategoryTotal]
    monthly_trend: list[MoneyMonthlyTotal]
    largest_expenses: list[MoneyTransactionResponse]
