from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserProfile
from ..schemas import UserProfileResponse, UserProfileUpdate
from ..security import get_current_active_user


router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


def get_profile(
    user_id: int,
    db: Session
) -> UserProfile:
    profile = db.scalar(
        select(UserProfile).where(
            UserProfile.user_id == user_id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    return profile


@router.get(
    "/me",
    response_model=UserProfileResponse
)
def read_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    return get_profile(
        current_user.id,
        db
    )


@router.patch(
    "/me",
    response_model=UserProfileResponse
)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    profile = get_profile(
        current_user.id,
        db
    )

    update_data = profile_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one profile field to update"
        )

    required_fields = {
        "timezone",
        "preferred_currency"
    }

    for field in required_fields:
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null"
            )

    preference_fields = {
        "ai_preferences",
        "privacy_preferences",
        "notification_preferences"
    }

    for field in preference_fields:
        if field in update_data and update_data[field] is None:
            update_data[field] = {}

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile
