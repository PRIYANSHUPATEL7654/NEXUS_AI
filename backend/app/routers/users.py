from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserResponse, UserUpdate
from ..security import get_current_active_user


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def require_own_profile(
    requested_user_id: int,
    current_user: User
) -> None:
    if requested_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own user profile"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def read_user(
    user_id: int,
    current_user: User = Depends(
        get_current_active_user
    )
):
    require_own_profile(user_id, current_user)
    return current_user


@router.patch(
    "/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    require_own_profile(user_id, current_user)

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update"
        )

    if any(value is None for value in update_data.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User fields cannot be null"
        )

    if "email" in update_data:
        update_data["email"] = str(
            update_data["email"]
        ).lower()

    for field, value in update_data.items():
        setattr(current_user, field, value)

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

    return current_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    require_own_profile(user_id, current_user)

    db.delete(current_user)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
