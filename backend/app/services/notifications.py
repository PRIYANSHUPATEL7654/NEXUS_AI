from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ImportJob, Notification, User, WorkTask


def _preferences_allow(user: User, kind: str) -> bool:
    preferences = user.profile.notification_preferences if user.profile else {}
    if preferences.get("in_app_enabled") is False:
        return False
    if kind.startswith("import_") and preferences.get("import_updates") is False:
        return False
    if kind == "task_overdue" and preferences.get("work_reminders") is False:
        return False
    return True


def _candidate_notifications(db: Session, user: User, today: date) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    imports = db.scalars(
        select(ImportJob).where(
            ImportJob.user_id == user.id,
            ImportJob.status.in_(["awaiting_review", "failed"]),
        )
    ).all()
    for job in imports:
        if job.status == "awaiting_review" and _preferences_allow(user, "import_review"):
            candidates.append({
                "kind": "import_review", "module": job.target_module,
                "title": f"{job.target_module.title()} import needs review",
                "message": "Review the extracted draft before any records are created.",
                "severity": "warning", "route": f"/{job.target_module}",
                "dedupe_key": f"import:{job.id}:awaiting_review",
            })
        elif job.status == "failed" and _preferences_allow(user, "import_failed"):
            candidates.append({
                "kind": "import_failed", "module": job.target_module,
                "title": f"{job.target_module.title()} import failed",
                "message": job.failure_reason or "The import could not be processed. Open the module to retry it.",
                "severity": "urgent", "route": f"/{job.target_module}",
                "dedupe_key": f"import:{job.id}:failed",
            })

    if _preferences_allow(user, "task_overdue"):
        tasks = db.scalars(
            select(WorkTask).where(
                WorkTask.user_id == user.id,
                WorkTask.due_date < today,
                WorkTask.status.notin_(["completed", "cancelled"]),
            )
        ).all()
        for task in tasks:
            candidates.append({
                "kind": "task_overdue", "module": "work",
                "title": "Work task is overdue", "message": task.title,
                "severity": "urgent", "route": "/work",
                "dedupe_key": f"work-task:{task.id}:overdue:{task.due_date}",
            })
    return candidates


def sync_notifications(db: Session, user: User, today: date | None = None) -> int:
    candidates = _candidate_notifications(db, user, today or date.today())
    if not candidates:
        return 0
    keys = [item["dedupe_key"] for item in candidates]
    existing = set(db.scalars(select(Notification.dedupe_key).where(
        Notification.user_id == user.id,
        Notification.dedupe_key.in_(keys),
    )).all())
    created = 0
    for item in candidates:
        if item["dedupe_key"] in existing:
            continue
        db.add(Notification(user_id=user.id, **item))
        created += 1
    if created:
        db.commit()
    return created


def unread_count(db: Session, user_id: int) -> int:
    return int(db.scalar(select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    )) or 0)
