from typing import List
from fastapi import APIRouter
from starlette import status

from app.domain.models.users import Users
from app.presentation.schemas.email_thread import EmailThreadResponse, EmailThreadCreate
from core.dependency_injection import EmailThreadServiceDependency, CurrentUserDependency, EmailThreadOrchestratorDependency

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