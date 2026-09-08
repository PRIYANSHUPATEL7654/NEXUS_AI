from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import (
    KnowledgeDocument, KnowledgeSummary, LearningGoal, LearningTopic,
    MoneyTransaction, User, WorkProject, WorkTask,
)


TOOL_REGISTRY = {
    "search_user_documents": {
        "description": "Search the authenticated user's Knowledge documents.",
        "required_parameters": ["query"], "optional_parameters": ["limit"],
    },
    "summarize_document": {
        "description": "Retrieve the latest saved summary for an owned document.",
        "required_parameters": ["document_id"], "optional_parameters": [],
    },
    "get_learning_progress": {
        "description": "Read goals, topics, progress levels and skill gaps.",
        "required_parameters": [], "optional_parameters": ["limit"],
    },
    "get_revision_queue": {
        "description": "Rank learning topics by remaining skill gap.",
        "required_parameters": [], "optional_parameters": ["limit"],
    },
    "get_money_summary": {
        "description": "Calculate income, expenses and net for one month.",
        "required_parameters": [], "optional_parameters": ["year", "month", "currency"],
    },
    "get_budget_status": {
        "description": "Compare monthly expenses with a caller-supplied local budget.",
        "required_parameters": ["monthly_limit"], "optional_parameters": ["year", "month", "currency"],
    },
    "get_pending_tasks": {
        "description": "Read owned pending Work tasks ordered by urgency.",
        "required_parameters": [], "optional_parameters": ["limit"],
    },
    "get_project_progress": {
        "description": "Calculate progress and remaining estimate for an owned Work project.",
        "required_parameters": ["project_id"], "optional_parameters": [],
    },
}


def _safe_timezone(user: User) -> tuple[ZoneInfo, str]:
    timezone_name = user.profile.timezone if user.profile else "UTC"
    try:
        return ZoneInfo(timezone_name), timezone_name
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC"), "UTC"


def _snippet(text: str | None, query: str, size: int = 180) -> str:
    clean = " ".join((text or "").split())
    if not clean:
        return ""
    index = clean.lower().find(query.lower())
    start = max(0, index - 50) if index >= 0 else 0
    result = clean[start:start + size]
    return ("..." if start else "") + result + ("..." if start + size < len(clean) else "")


def _score(query: str, title: str, body: str | None) -> int:
    terms = [term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 1]
    title_lower = title.lower()
    body_lower = (body or "").lower()
    return sum(5 for term in terms if term in title_lower) + sum(1 for term in terms if term in body_lower)


def cross_module_search(db: Session, user_id: int, query: str, limit: int = 20) -> dict[str, Any]:
    query = query.strip()
    if len(query) < 2:
        raise ValueError("Search query must contain at least two characters")
    pattern = f"%{query}%"
    results: list[dict[str, Any]] = []

    documents = db.scalars(select(KnowledgeDocument).where(
        KnowledgeDocument.user_id == user_id,
        or_(KnowledgeDocument.title.ilike(pattern), KnowledgeDocument.description.ilike(pattern), KnowledgeDocument.extracted_text.ilike(pattern)),
    ).limit(limit)).all()
    for item in documents:
        results.append({
            "module": "knowledge", "record_type": "document", "record_id": item.id,
            "title": item.title, "snippet": _snippet(item.description or item.extracted_text, query),
            "score": _score(query, item.title, item.description or item.extracted_text),
            "route": f"/knowledge/documents/{item.id}",
        })

    topics = db.scalars(select(LearningTopic).where(
        LearningTopic.user_id == user_id,
        or_(LearningTopic.title.ilike(pattern), LearningTopic.description.ilike(pattern)),
    ).limit(limit)).all()
    for item in topics:
        results.append({
            "module": "learn", "record_type": "topic", "record_id": item.id,
            "title": item.title, "snippet": _snippet(item.description, query),
            "score": _score(query, item.title, item.description), "route": "/learn",
        })

    transactions = db.scalars(select(MoneyTransaction).where(
        MoneyTransaction.user_id == user_id,
        or_(MoneyTransaction.description.ilike(pattern), MoneyTransaction.category.ilike(pattern)),
    ).limit(limit)).all()
    for item in transactions:
        results.append({
            "module": "money", "record_type": "transaction", "record_id": item.id,
            "title": item.description, "snippet": f"{item.transaction_date} - {item.currency} {item.amount} - {item.category}",
            "score": _score(query, item.description, item.category), "route": "/money",
        })

    projects = db.scalars(select(WorkProject).where(
        WorkProject.user_id == user_id,
        or_(WorkProject.title.ilike(pattern), WorkProject.description.ilike(pattern)),
    ).limit(limit)).all()
    for item in projects:
        results.append({
            "module": "work", "record_type": "project", "record_id": item.id,
            "title": item.title, "snippet": _snippet(item.description, query),
            "score": _score(query, item.title, item.description), "route": "/work",
        })

    tasks = db.scalars(select(WorkTask).where(
        WorkTask.user_id == user_id,
        or_(WorkTask.title.ilike(pattern), WorkTask.description.ilike(pattern), WorkTask.notes.ilike(pattern)),
    ).limit(limit)).all()
    for item in tasks:
        results.append({
            "module": "work", "record_type": "task", "record_id": item.id,
            "title": item.title, "snippet": _snippet(item.description or item.notes, query),
            "score": _score(query, item.title, item.description or item.notes), "route": "/work",
        })

    ranked = sorted(results, key=lambda item: (-item["score"], item["module"], item["record_id"]))[:limit]
    return {"query": query, "total": len(ranked), "results": ranked}


def learning_progress(db: Session, user_id: int, limit: int = 10) -> dict[str, Any]:
    goals = list(db.scalars(select(LearningGoal).where(
        LearningGoal.user_id == user_id, LearningGoal.status == "active"
    ).order_by(LearningGoal.priority.desc(), LearningGoal.created_at).limit(limit)).all())
    topics = list(db.scalars(select(LearningTopic).where(
        LearningTopic.user_id == user_id
    ).order_by((LearningTopic.target_level - LearningTopic.current_level).desc()).limit(limit)).all())
    return {
        "active_goal_count": len(goals),
        "goals": [{"id": item.id, "title": item.title, "priority": item.priority, "target_date": item.target_date} for item in goals],
        "topics": [{
            "id": item.id, "goal_id": item.goal_id, "title": item.title,
            "current_level": item.current_level, "target_level": item.target_level,
            "skill_gap": max(0, item.target_level - item.current_level), "status": item.status,
        } for item in topics],
    }


def revision_queue(db: Session, user_id: int, limit: int = 5) -> dict[str, Any]:
    topics = list(db.scalars(select(LearningTopic).where(
        LearningTopic.user_id == user_id,
        LearningTopic.status != "mastered",
        LearningTopic.current_level < LearningTopic.target_level,
    ).order_by((LearningTopic.target_level - LearningTopic.current_level).desc()).limit(limit)).all())
    return {"items": [{
        "topic_id": item.id, "title": item.title,
        "current_level": item.current_level, "target_level": item.target_level,
        "skill_gap": item.target_level - item.current_level,
        "reason": "Target level is higher than the recorded current level",
    } for item in topics]}


def money_summary(db: Session, user_id: int, local_date: date, currency: str = "INR", year: int | None = None, month: int | None = None) -> dict[str, Any]:
    selected_year = int(year) if year is not None else local_date.year
    selected_month = int(month) if month is not None else local_date.month
    if selected_year < 1900 or selected_year > 2200:
        raise ValueError("year must be between 1900 and 2200")
    if not 1 <= selected_month <= 12:
        raise ValueError("month must be between 1 and 12")
    first = date(selected_year, selected_month, 1)
    last = date(selected_year, selected_month, monthrange(selected_year, selected_month)[1])
    rows = list(db.scalars(select(MoneyTransaction).where(
        MoneyTransaction.user_id == user_id,
        MoneyTransaction.currency == currency.upper(),
        MoneyTransaction.transaction_date >= first,
        MoneyTransaction.transaction_date <= last,
    )).all())
    income = sum((row.amount for row in rows if row.transaction_type == "income"), Decimal("0"))
    expenses = sum((row.amount for row in rows if row.transaction_type == "expense"), Decimal("0"))
    return {
        "year": selected_year, "month": selected_month, "currency": currency.upper(),
        "income": income, "expenses": expenses, "net": income - expenses,
        "transaction_count": len(rows),
    }


def pending_tasks(db: Session, user_id: int, local_date: date, limit: int = 10) -> dict[str, Any]:
    tasks = list(db.scalars(select(WorkTask).where(
        WorkTask.user_id == user_id,
        WorkTask.status.notin_(["completed", "cancelled"]),
    ).order_by(WorkTask.due_date.asc().nullslast(), WorkTask.priority.desc()).limit(limit)).all())
    return {"items": [{
        "task_id": item.id, "project_id": item.project_id, "title": item.title,
        "status": item.status, "priority": item.priority, "due_date": item.due_date,
        "overdue": item.due_date is not None and item.due_date < local_date,
        "estimated_minutes_low": item.estimated_minutes_low,
        "estimated_minutes_high": item.estimated_minutes_high,
    } for item in tasks]}


def project_progress(db: Session, user_id: int, project_id: int) -> dict[str, Any]:
    project = db.scalar(select(WorkProject).where(WorkProject.id == project_id, WorkProject.user_id == user_id))
    if project is None:
        raise LookupError("Work project not found")
    tasks = list(db.scalars(select(WorkTask).where(
        WorkTask.project_id == project.id, WorkTask.user_id == user_id
    )).all())
    completed = [task for task in tasks if task.status == "completed"]
    pending = [task for task in tasks if task.status not in {"completed", "cancelled"}]
    progress = round((len(completed) / len(tasks)) * 100) if tasks else 0
    return {
        "project_id": project.id, "title": project.title, "status": project.status,
        "task_count": len(tasks), "completed_task_count": len(completed),
        "progress_percent": progress,
        "remaining_minutes_low": sum(task.estimated_minutes_low for task in pending),
        "remaining_minutes_high": sum(task.estimated_minutes_high for task in pending),
    }


def latest_document_summary(db: Session, user_id: int, document_id: int) -> dict[str, Any]:
    document = db.scalar(select(KnowledgeDocument).where(
        KnowledgeDocument.id == document_id, KnowledgeDocument.user_id == user_id
    ))
    if document is None:
        raise LookupError("Knowledge document not found")
    summary = db.scalar(select(KnowledgeSummary).where(
        KnowledgeSummary.document_id == document.id,
        KnowledgeSummary.user_id == user_id,
    ).order_by(KnowledgeSummary.created_at.desc()))
    return {
        "document_id": document.id, "title": document.title,
        "summary_available": summary is not None,
        "summary_id": summary.id if summary else None,
        "summary_type": summary.summary_type if summary else None,
        "content": summary.content if summary else None,
        "message": None if summary else "Generate a summary in Nexus Knowledge first",
    }


def recommendations(db: Session, user: User) -> dict[str, Any]:
    timezone, _ = _safe_timezone(user)
    local_date = datetime.now(timezone).date()
    items: list[dict[str, Any]] = []
    revisions = revision_queue(db, user.id, 3)["items"]
    if revisions:
        top = revisions[0]
        items.append({
            "module": "learn", "priority": 4, "title": f"Revise {top['title']}",
            "reason": "This topic has the largest recorded skill gap.",
            "evidence": [f"Current {top['current_level']}%, target {top['target_level']}%", f"Gap {top['skill_gap']} points"],
            "action": "Review the linked Knowledge document and take a quiz.", "route": "/learn",
        })
    pending = pending_tasks(db, user.id, local_date, 20)["items"]
    overdue = [item for item in pending if item["overdue"]]
    if overdue:
        items.append({
            "module": "work", "priority": 5, "title": f"Resolve {len(overdue)} overdue Work task(s)",
            "reason": "Due dates have passed while the tasks remain open.",
            "evidence": [item["title"] for item in overdue[:3]],
            "action": "Complete, reschedule or mark the blocking reason.", "route": "/work",
        })
    elif pending:
        first = pending[0]
        items.append({
            "module": "work", "priority": first["priority"], "title": first["title"],
            "reason": "This is the next pending task by due date and priority.",
            "evidence": [f"Due {first['due_date'] or 'not set'}", f"Estimate {first['estimated_minutes_low']}-{first['estimated_minutes_high']} minutes"],
            "action": "Start or continue this task.", "route": "/work",
        })
    currency = user.profile.preferred_currency if user.profile else "INR"
    money = money_summary(db, user.id, local_date, currency)
    if money["expenses"] > money["income"] and money["expenses"] > 0:
        items.append({
            "module": "money", "priority": 3, "title": "Review this month's spending",
            "reason": "Recorded expenses are above recorded income for the current month.",
            "evidence": [f"Income {currency} {money['income']}", f"Expenses {currency} {money['expenses']}"],
            "action": "Check categories and missing income entries before drawing conclusions.", "route": "/money",
        })
    document_count = len(db.scalars(select(KnowledgeDocument.id).where(KnowledgeDocument.user_id == user.id)).all())
    if document_count == 0:
        items.append({
            "module": "knowledge", "priority": 2, "title": "Add your first Knowledge document",
            "reason": "Nexus has no approved document to search or summarize.",
            "evidence": ["Knowledge document count is zero"],
            "action": "Upload a useful learning or reference document.", "route": "/knowledge",
        })
    return {"generated_for": local_date, "recommendations": sorted(items, key=lambda item: item["priority"], reverse=True)}


def daily_brief(db: Session, user: User) -> dict[str, Any]:
    timezone, timezone_name = _safe_timezone(user)
    now = datetime.now(timezone)
    local_date = now.date()
    currency = user.profile.preferred_currency if user.profile else "INR"
    learning = revision_queue(db, user.id, 5)["items"]
    work = pending_tasks(db, user.id, local_date, 20)["items"]
    money = money_summary(db, user.id, local_date, currency)
    document_count = len(db.scalars(select(KnowledgeDocument.id).where(KnowledgeDocument.user_id == user.id)).all())
    overdue_count = sum(item["overdue"] for item in work)
    sections = [
        {
            "title": "Learning", "value": f"{len(learning)} topic(s) need attention",
            "detail": learning[0]["title"] if learning else "No active skill gap was found",
            "severity": "warning" if learning else "success", "route": "/learn",
        },
        {
            "title": "Work", "value": f"{len(work)} pending task(s)",
            "detail": f"{overdue_count} overdue" if overdue_count else (work[0]["title"] if work else "No pending tasks"),
            "severity": "urgent" if overdue_count else "info", "route": "/work",
        },
        {
            "title": "Money", "value": f"{currency} {money['expenses']} spent this month",
            "detail": f"Net recorded amount: {currency} {money['net']}",
            "severity": "warning" if money["expenses"] > money["income"] and money["expenses"] else "info", "route": "/money",
        },
        {
            "title": "Knowledge", "value": f"{document_count} saved document(s)",
            "detail": "Search and summaries use only your owned records",
            "severity": "info", "route": "/knowledge",
        },
    ]
    focus_parts = []
    if overdue_count:
        focus_parts.append(f"resolve {overdue_count} overdue task(s)")
    if learning:
        focus_parts.append(f"revise {learning[0]['title']}")
    summary = "Today, " + " and ".join(focus_parts) + "." if focus_parts else "Your recorded plan has no urgent item today."
    greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
    return {
        "local_date": local_date, "timezone": timezone_name,
        "greeting": f"{greeting}, {user.name}", "summary": summary, "sections": sections,
    }


def run_tool(db: Session, user: User, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError("Unknown or disabled Intelligence tool")
    timezone, _ = _safe_timezone(user)
    local_date = datetime.now(timezone).date()
    if tool_name == "search_user_documents":
        query = str(parameters.get("query", "")).strip()
        result = cross_module_search(db, user.id, query, max(1, min(int(parameters.get("limit", 10)), 50)))
        result["results"] = [item for item in result["results"] if item["module"] == "knowledge"]
        result["total"] = len(result["results"])
        return result
    if tool_name == "summarize_document":
        return latest_document_summary(db, user.id, int(parameters["document_id"]))
    if tool_name == "get_learning_progress":
        return learning_progress(db, user.id, max(1, min(int(parameters.get("limit", 10)), 50)))
    if tool_name == "get_revision_queue":
        return revision_queue(db, user.id, max(1, min(int(parameters.get("limit", 5)), 50)))
    if tool_name == "get_money_summary":
        return money_summary(db, user.id, local_date, str(parameters.get("currency", user.profile.preferred_currency if user.profile else "INR")), parameters.get("year"), parameters.get("month"))
    if tool_name == "get_budget_status":
        limit = Decimal(str(parameters["monthly_limit"]))
        if limit <= 0:
            raise ValueError("monthly_limit must be positive")
        money = money_summary(db, user.id, local_date, str(parameters.get("currency", user.profile.preferred_currency if user.profile else "INR")), parameters.get("year"), parameters.get("month"))
        money.update({"monthly_limit": limit, "remaining": limit - money["expenses"], "over_budget": money["expenses"] > limit})
        return money
    if tool_name == "get_pending_tasks":
        return pending_tasks(db, user.id, local_date, max(1, min(int(parameters.get("limit", 10)), 50)))
    if tool_name == "get_project_progress":
        return project_progress(db, user.id, int(parameters["project_id"]))
    raise KeyError("Unknown or disabled Intelligence tool")


def ask_nexus(db: Session, user: User, message: str) -> tuple[str, str, list[str], dict[str, Any]]:
    lowered = message.lower()
    timezone, _ = _safe_timezone(user)
    local_date = datetime.now(timezone).date()
    if any(word in lowered for word in ["today", "focus", "daily", "brief"]):
        data = daily_brief(db, user)
        return "daily_brief", data["summary"], ["daily_brief"], data
    if any(word in lowered for word in ["spend", "spent", "expense", "money", "income"]):
        currency = user.profile.preferred_currency if user.profile else "INR"
        data = money_summary(db, user.id, local_date, currency)
        answer = f"This month you recorded {currency} {data['income']} income and {currency} {data['expenses']} expenses, for a net of {currency} {data['net']}."
        return "money_summary", answer, ["get_money_summary"], data
    if any(word in lowered for word in ["learn", "study", "revision", "skill", "quiz"]):
        data = revision_queue(db, user.id, 5)
        answer = f"I found {len(data['items'])} learning topic(s) that need attention."
        return "learning_progress", answer, ["get_revision_queue"], data
    if any(word in lowered for word in ["work", "task", "deadline", "project", "pending"]):
        data = pending_tasks(db, user.id, local_date, 10)
        answer = f"You have {len(data['items'])} pending task(s) in the current result."
        return "pending_work", answer, ["get_pending_tasks"], data
    data = cross_module_search(db, user.id, message, 10)
    answer = f"I found {data['total']} matching record(s) across your NEXUS modules."
    return "search", answer, ["cross_module_search"], data
