import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from dateutil import parser as date_parser


ACTION_WORDS = {
    "analyze", "build", "configure", "create", "deploy", "design", "develop",
    "document", "implement", "integrate", "prepare", "review", "test", "update",
    "validate", "write", "submit", "fix", "install", "migrate", "research",
}
COMPLEX_WORDS = {"deploy", "implement", "integrate", "migrate", "architecture", "security", "database", "api"}
SIMPLE_WORDS = {"read", "review", "rename", "update", "submit", "document"}


@dataclass(frozen=True)
class ProposedWorkTask:
    title: str
    description: str | None
    priority: int
    complexity: int
    due_date: date | None
    estimated_minutes_low: int
    estimated_minutes_high: int
    confidence: Decimal
    source_location: str
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkPlanResult:
    project_title: str
    tasks: list[ProposedWorkTask]
    estimated_minutes_low: int
    estimated_minutes_high: int
    estimate_confidence: str
    assumptions: list[str]
    warnings: list[str]


def _clean_line(line: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()


def _extract_due_date(text: str) -> date | None:
    match = re.search(
        r"(?i)\b(?:due|deadline|by)\s*[:\-]?\s*(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        text,
    )
    if not match:
        return None
    try:
        return date_parser.parse(match.group(1), dayfirst=True).date()
    except (ValueError, OverflowError):
        return None


def _complexity(text: str) -> int:
    lowered = text.lower()
    word_count = len(lowered.split())
    score = 2
    if any(word in lowered for word in COMPLEX_WORDS):
        score += 1
    if sum(word in lowered for word in COMPLEX_WORDS) >= 2 or word_count > 30:
        score += 1
    if any(word in lowered for word in SIMPLE_WORDS) and not any(word in lowered for word in COMPLEX_WORDS):
        score -= 1
    return max(1, min(5, score))


def _estimate_minutes(complexity: int, text: str) -> tuple[int, int]:
    base = {1: 20, 2: 45, 3: 90, 4: 180, 5: 300}[complexity]
    if "test" in text.lower() or "validate" in text.lower():
        base += 30
    return base, int(base * 1.6)


def parse_work_plan(text: str, fallback_title: str = "Imported work plan") -> WorkPlanResult:
    meaningful = [
        _clean_line(line)
        for line in text.splitlines()
        if _clean_line(line) and not _clean_line(line).startswith("--- Page") and not _clean_line(line).startswith("--- Sheet")
    ]
    if not meaningful:
        raise ValueError("The document did not contain readable work instructions")

    project_title = meaningful[0][:200]
    if len(project_title.split()) > 14:
        project_title = fallback_title[:200]

    candidates: list[tuple[int, str]] = []
    for line_number, line in enumerate(meaningful[1:], start=2):
        lowered_words = set(re.findall(r"[a-z]+", line.lower()))
        looks_like_bullet = bool(re.match(r"^\s*(?:[-*•]|\d+[.)])", text.splitlines()[min(line_number - 1, len(text.splitlines()) - 1)]))
        if lowered_words & ACTION_WORDS or looks_like_bullet:
            candidates.append((line_number, line))

    if not candidates:
        joined = " ".join(meaningful[1:])
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", joined) if len(part.strip()) >= 8]
        candidates = [(index + 2, sentence) for index, sentence in enumerate(sentences[:12])]
    if not candidates:
        raise ValueError("No actionable tasks could be proposed from the document")

    tasks: list[ProposedWorkTask] = []
    for line_number, candidate in candidates[:30]:
        complexity = _complexity(candidate)
        low, high = _estimate_minutes(complexity, candidate)
        due_date = _extract_due_date(candidate)
        priority = 5 if re.search(r"(?i)\b(urgent|critical|must)\b", candidate) else 3
        warnings: list[str] = []
        confidence = Decimal("0.85")
        if due_date is None:
            warnings.append("No explicit due date found")
            confidence -= Decimal("0.10")
        if len(candidate.split()) < 4:
            warnings.append("Task description is short; review the scope")
            confidence -= Decimal("0.10")
        tasks.append(ProposedWorkTask(
            title=candidate[:300], description=None, priority=priority,
            complexity=complexity, due_date=due_date,
            estimated_minutes_low=low, estimated_minutes_high=high,
            confidence=confidence, source_location=f"Extracted line {line_number}",
            warnings=warnings,
        ))

    total_low = sum(task.estimated_minutes_low for task in tasks)
    total_high = sum(task.estimated_minutes_high for task in tasks)
    explicit_dates = sum(task.due_date is not None for task in tasks)
    confidence = "high" if explicit_dates == len(tasks) and len(tasks) >= 3 else "medium" if len(tasks) >= 3 else "low"
    assumptions = [
        "One person performs the work",
        "Required access, data and approvals are available",
        "The estimate includes task execution but not external waiting time",
        "Every proposed task will be reviewed before approval",
    ]
    warnings = [] if len(tasks) >= 2 else ["Only one task was detected; the document may need manual breakdown"]
    return WorkPlanResult(
        project_title=project_title, tasks=tasks,
        estimated_minutes_low=total_low, estimated_minutes_high=total_high,
        estimate_confidence=confidence, assumptions=assumptions, warnings=warnings,
    )
