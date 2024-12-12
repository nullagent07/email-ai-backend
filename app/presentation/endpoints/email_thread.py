from typing import List
from fastapi import APIRouter
from starlette import status

from app.domain.models.users import Users
from app.presentation.schemas.email_thread import EmailThreadResponse
from core.dependency_injection import EmailThreadServiceDependency, CurrentUserDependency

router = APIRouter(prefix="/email-threads", tags=["email-threads"])


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
        )
        for thread in threads
    ]