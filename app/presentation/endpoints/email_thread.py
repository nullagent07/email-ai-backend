from typing import List
from fastapi import APIRouter, Request, HTTPException
from starlette import status

from app.domain.models.users import Users
from app.presentation.schemas.email_thread import EmailThreadResponse, EmailThreadCreate
from app.applications.services.auth.google_auth_service import GoogleAuthenticationService
from app.infrastructure.integrations.auth.google.adapter import GoogleAuthAdapter
from core.dependency_injection import (
    EmailThreadServiceDependency, 
    CurrentUserDependency, 
    EmailThreadOrchestratorDependency,
    AccessTokenDependency
)

router = APIRouter(prefix="/email-threads", tags=["email-threads"])
google_auth = GoogleAuthenticationService(GoogleAuthAdapter())


@router.get(
    "/{assistant_id}",
    response_model=List[EmailThreadResponse],
    status_code=status.HTTP_200_OK,
)
async def get_threads(
    assistant_id: str,
    current_user: CurrentUserDependency,
    email_thread_service: EmailThreadServiceDependency,
) -> List[EmailThreadResponse]:
    """Get all email threads for the current user and assistant."""
    threads = await email_thread_service.get_threads_by_user_and_assistant(
        current_user, assistant_id
    )
    return [
        EmailThreadResponse(
            id=thread.id,
            user_email=thread.user_email,
            recipient_email=thread.recipient_email,
            recipient_name=thread.recipient_name,
            assistant_profile_id=thread.assistant_profile_id,
            instructions=thread.instructions,
            status=thread.status,
        )
        for thread in threads
    ]


@router.post(
    "/{assistant_id}",
    response_model=EmailThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    assistant_id: str,
    thread_data: EmailThreadCreate,
    current_user: CurrentUserDependency,
    email_thread_orchestrator: EmailThreadOrchestratorDependency,
) -> EmailThreadResponse:
    """Create a new email thread."""
    thread = await email_thread_orchestrator.create_thread_with_openai(
        user_id=current_user,
        assistant_id=assistant_id,
        thread_data=thread_data
    )
    return EmailThreadResponse(
        id=thread.id,
        user_email=thread.user_email,
        recipient_email=thread.recipient_email,
        recipient_name=thread.recipient_name,
        assistant_profile_id=thread.assistant_profile_id,
        instructions=thread.instructions,
        status=thread.status,
    )


@router.post(
    "/status/{assistant_id}/{thread_id}",
    status_code=status.HTTP_200_OK,
)
async def start_thread(
    assistant_id: str,
    thread_id: str,
    current_user: CurrentUserDependency,
    access_token: AccessTokenDependency,
    email_thread_orchestrator: EmailThreadOrchestratorDependency,
) -> dict:
    """Start an existing email thread with Gmail watch."""
    await email_thread_orchestrator.run_thread_with_gmail_watch(
        user_id=current_user,
        access_token=access_token,
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return {"status": "success", "message": "Thread started successfully"}


@router.post(
    "/gmail/webhook",
    status_code=status.HTTP_200_OK,
)
async def gmail_webhook(
    request: Request,
    email_thread_orchestrator: EmailThreadOrchestratorDependency,
):
    """
    Handle Gmail push notifications.
    This endpoint receives notifications when emails are received or modified.
    """
    # Verify JWT token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = auth_header.split(" ")[1]
    try:
        # Validate the token using Google Auth service
        await google_auth.validate_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

    # Parse the notification data
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON data: {str(e)}"
        )
    
    # Handle the notification
    try:
        await email_thread_orchestrator.handle_gmail_notification(data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Gmail notification: {str(e)}"
        )