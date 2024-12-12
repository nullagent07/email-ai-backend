from typing import List
from uuid import UUID

from app.domain.interfaces.repositories.email_thread_repository import IEmailThreadRepository
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.models.email_threads import EmailThreads


class EmailThreadService(IEmailThreadService):
    """Service for email threads."""

    def __init__(self, repository: IEmailThreadRepository) -> None:
        self._repository = repository

    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        return await self._repository.get_threads_by_user_and_assistant(user_id, assistant_id)
