from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification, User
from ..notification_schemas import (
    NotificationCountResponse, NotificationReadAllResponse,
    NotificationResponse, NotificationSyncResponse,
)
from ..security import get_current_active_user
from ..services.notifications import sync_notifications, unread_count


router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _owned_notification(db: Session, user_id: int, notification_id: int) -> Notification:
    item = db.scalar(select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item


@router.post("/sync", response_model=NotificationSyncResponse)
def sync_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    created = sync_notifications(db, current_user)
    return {"created_count": created, "unread_count": unread_count(db, current_user.id)}


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    statement = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    return list(db.scalars(statement.order_by(Notification.created_at.desc()).limit(limit)).all())


@router.get("/unread-count", response_model=NotificationCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return {"unread_count": unread_count(db, current_user.id)}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = _owned_notification(db, current_user.id, notification_id)
    if not item.is_read:
        item.is_read = True
        item.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item


@router.post("/read-all", response_model=NotificationReadAllResponse)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = db.execute(
        update(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        ).values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    db.commit()
    return {"updated_count": result.rowcount or 0}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    item = _owned_notification(db, current_user.id, notification_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
