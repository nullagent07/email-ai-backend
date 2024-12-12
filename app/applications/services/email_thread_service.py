from typing import List
from uuid import UUID

from app.domain.interfaces.repositories.email_thread_repository import IEmailThreadRepository
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.interfaces.services.user_service import IUserService
from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate


class EmailThreadService(IEmailThreadService):
    """Service for email threads."""

    def __init__(
        self,
        repository: IEmailThreadRepository,
        user_service: IUserService
    ) -> None:
        self._repository = repository
        self._user_service = user_service

    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        return await self._repository.get_threads_by_user_and_assistant(user_id, assistant_id)

    async def create_thread(
        self,
        user_id: UUID,
        user_email: str | None,
        assistant_id: str,
        thread_data: EmailThreadCreate,
        thread_id: str,
    ) -> EmailThreads:
        """Create a new email thread."""
        if user_email is None:
            user = await self._user_service.find_user_by_id(user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            user_email = user.email

        return await self._repository.create_thread(
            user_id=user_id,
            user_email=user_email,
            assistant_id=assistant_id,
            thread_data=thread_data,
            thread_id=thread_id,
        )
