from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


NotificationModule = Literal["knowledge", "learn", "money", "work", "system"]
NotificationSeverity = Literal["info", "success", "warning", "urgent"]


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    kind: str
    module: NotificationModule
    title: str
    message: str
    severity: NotificationSeverity
    route: str | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class NotificationCountResponse(BaseModel):
    unread_count: int


class NotificationSyncResponse(BaseModel):
    created_count: int
    unread_count: int


class NotificationReadAllResponse(BaseModel):
    updated_count: int
