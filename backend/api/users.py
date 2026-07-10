from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.utils.security import get_current_user
from shared.db.models import get_db, User
from shared.schemas import UserProfileResponse, UserProfileUpdateRequest

router = APIRouter(tags=["users"])

@router.get("/users/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)) -> User:
    """
    Retrieve the profile details of the currently authenticated user.
    """
    return current_user

@router.put("/users/me", response_model=UserProfileResponse)
def update_my_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Update the authenticated user's preferences and profile settings.
    """
    update_data = payload.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user
