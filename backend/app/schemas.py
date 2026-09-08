from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class UserBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    age: int = Field(
        ge=1,
        le=120
    )


class UserRegister(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    email: EmailStr | None = None

    age: int | None = Field(
        default=None,
        ge=1,
        le=120
    )


class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class UserProfileUpdate(BaseModel):
    timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    preferred_currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$"
    )

    learning_goals: str | None = Field(
        default=None,
        max_length=5000
    )

    work_preferences: str | None = Field(
        default=None,
        max_length=5000
    )

    ai_preferences: dict[str, Any] | None = None
    privacy_preferences: dict[str, Any] | None = None
    notification_preferences: dict[str, Any] | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(
        cls,
        value: str | None
    ) -> str | None:
        if value is None:
            return value

        normalized_value = value.strip()

        try:
            ZoneInfo(normalized_value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(
                "Use a valid IANA timezone such as Asia/Kolkata or UTC"
            )

        return normalized_value

    @field_validator("preferred_currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str | None
    ) -> str | None:
        if value is None:
            return value

        return value.upper()


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    timezone: str
    preferred_currency: str
    learning_goals: str | None
    work_preferences: str | None
    ai_preferences: dict[str, Any]
    privacy_preferences: dict[str, Any]
    notification_preferences: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
