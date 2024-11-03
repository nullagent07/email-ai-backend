# app/endpoints/auth_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependency import get_current_user
from app.models.user import User
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return current_user