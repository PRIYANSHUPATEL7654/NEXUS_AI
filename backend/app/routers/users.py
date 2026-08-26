from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status
)

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        age=user_data.age
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    return new_user


@router.get(
    "",
    response_model=list[UserResponse]
)
def get_users(
    skip: int = Query(
        default=0,
        ge=0
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    db: Session = Depends(get_db)
):
    statement = (
        select(User)
        .offset(skip)
        .limit(limit)
    )

    users = db.scalars(statement).all()

    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update."
        )

    if any(value is None for value in update_data.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Updated fields cannot be null."
        )

    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    db.delete(user)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )