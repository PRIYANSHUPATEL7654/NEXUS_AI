import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser


CURRENCY_AMOUNT_PATTERN = re.compile(
    r"(?i)(?:₹|rs\.?\s*|inr\s+)([0-9][0-9,]*(?:\.\d{1,2})?)"
)
PLAIN_AMOUNT_PATTERN = re.compile(r"\b([0-9][0-9,]*(?:\.\d{1,2})?)\b")
EXPLICIT_DATE_PATTERN = re.compile(
    r"(?i)\b(?:on\s+)?(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"(?:\s+\d{4})?)\b"
)

INCOME_WORDS = {"received", "credited", "salary", "income", "earned", "refund", "reimbursed", "interest"}
CATEGORY_KEYWORDS = {
    "Food": {"food", "lunch", "dinner", "breakfast", "restaurant", "zomato", "swiggy", "grocery", "groceries", "cafe"},
    "Transport": {"uber", "ola", "taxi", "fuel", "petrol", "diesel", "bus", "train", "metro", "parking"},
    "Shopping": {"amazon", "flipkart", "shopping", "clothes", "shoes", "electronics"},
    "Bills": {"bill", "electricity", "internet", "wifi", "mobile", "recharge", "gas"},
    "Health": {"doctor", "hospital", "medicine", "medical", "pharmacy", "health"},
    "Education": {"course", "book", "exam", "college", "tuition", "education"},
    "Entertainment": {"movie", "netflix", "spotify", "game", "concert", "entertainment"},
    "Housing": {"rent", "maintenance", "furniture", "housing"},
    "Salary": {"salary", "payroll", "stipend"},
    "Transfer": {"transfer", "sent to", "upi transfer"},
}


@dataclass(frozen=True)
class ParsedTransaction:
    transaction_date: date
    description: str
    amount: Decimal
    transaction_type: str
    category: str
    confidence: Decimal
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParseResult:
    transactions: list[ParsedTransaction]
    warnings: list[str]


def _split_entries(text: str) -> list[str]:
    normalized = text.replace("\r", "\n")
    parts = re.split(r"\n+|;", normalized)
    return [part.strip(" -•\t") for part in parts if part.strip(" -•\t")]


def _parse_date(entry: str, today: date) -> tuple[date, bool]:
    lowered = entry.lower()
    if "yesterday" in lowered:
        return today - timedelta(days=1), True
    if re.search(r"\btoday\b", lowered):
        return today, True

    match = EXPLICIT_DATE_PATTERN.search(entry)
    if match:
        try:
            parsed = date_parser.parse(match.group(1), dayfirst=True, default=datetime.combine(today, datetime.min.time()))
            return parsed.date(), True
        except (ValueError, OverflowError):
            pass
    return today, False


def _category(entry: str, transaction_type: str) -> tuple[str, bool]:
    lowered = entry.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category, True
    if transaction_type == "income":
        return "Other", False
    return "Other", False


def _amount_text(entry: str) -> str | None:
    currency_match = CURRENCY_AMOUNT_PATTERN.search(entry)
    if currency_match:
        return currency_match.group(1)

    without_date = EXPLICIT_DATE_PATTERN.sub(" ", entry)
    candidates = PLAIN_AMOUNT_PATTERN.findall(without_date)
    for candidate in candidates:
        normalized = candidate.replace(",", "")
        if normalized.isdigit() and 1900 <= int(normalized) <= 2100:
            continue
        return candidate
    return None


def parse_transaction_text(text: str, today: date | None = None) -> ParseResult:
    reference_date = today or date.today()
    transactions: list[ParsedTransaction] = []
    batch_warnings: list[str] = []

    for line_number, entry in enumerate(_split_entries(text), start=1):
        amount_text = _amount_text(entry)
        if amount_text is None:
            batch_warnings.append(f"Line {line_number} was skipped because no amount was found")
            continue
        try:
            amount = Decimal(amount_text.replace(",", "")).quantize(Decimal("0.01"))
        except InvalidOperation:
            batch_warnings.append(f"Line {line_number} was skipped because its amount was invalid")
            continue
        if amount <= 0:
            batch_warnings.append(f"Line {line_number} was skipped because amount must be positive")
            continue

        lowered_words = set(re.findall(r"[a-z]+", entry.lower()))
        transaction_type = "income" if lowered_words & INCOME_WORDS else "expense"
        transaction_date, found_date = _parse_date(entry, reference_date)
        category, found_category = _category(entry, transaction_type)
        warnings: list[str] = []
        confidence = Decimal("0.55")
        if found_date:
            confidence += Decimal("0.20")
        else:
            warnings.append("No date found; today's date was proposed")
        if found_category:
            confidence += Decimal("0.20")
        else:
            warnings.append("No category keyword matched; Other was proposed")
        if lowered_words & INCOME_WORDS or lowered_words & {"paid", "spent", "bought", "debited", "purchase"}:
            confidence += Decimal("0.05")

        transactions.append(ParsedTransaction(
            transaction_date=transaction_date,
            description=entry[:500],
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            confidence=min(confidence, Decimal("1.000")),
            warnings=warnings,
        ))

    if not transactions:
        raise ValueError("No transactions with recognizable amounts were found")
    return ParseResult(transactions=transactions, warnings=batch_warnings)
