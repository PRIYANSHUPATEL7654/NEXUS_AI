import hashlib
import re
from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import MoneyTransaction


def normalize_description(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def transaction_fingerprint(
    transaction_date: date,
    amount: Decimal,
    transaction_type: str,
    description: str,
) -> str:
    normalized = "|".join(
        [
            transaction_date.isoformat(),
            f"{Decimal(amount):.2f}",
            transaction_type,
            normalize_description(description),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_possible_duplicate(
    db: Session,
    user_id: int,
    transaction_date: date,
    amount: Decimal,
    transaction_type: str,
    description: str,
) -> MoneyTransaction | None:
    candidates = db.scalars(
        select(MoneyTransaction).where(
            MoneyTransaction.user_id == user_id,
            MoneyTransaction.transaction_date == transaction_date,
            MoneyTransaction.amount == amount,
            MoneyTransaction.transaction_type == transaction_type,
        )
    ).all()

    wanted = normalize_description(description)
    for candidate in candidates:
        existing = normalize_description(candidate.description)
        if wanted == existing or SequenceMatcher(None, wanted, existing).ratio() >= 0.80:
            return candidate
    return None
