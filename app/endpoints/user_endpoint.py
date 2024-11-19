# app/endpoints/user_endpoint.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.services.user_service import UserService
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    user_service: UserService = Depends(UserService.get_instance)
):
    try:
        current_user = await user_service.get_current_user(request)
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
