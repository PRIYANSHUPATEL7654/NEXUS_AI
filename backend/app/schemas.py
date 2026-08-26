from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class UserCreate(UserBase):
    pass


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

    model_config = ConfigDict(
        from_attributes=True
    )