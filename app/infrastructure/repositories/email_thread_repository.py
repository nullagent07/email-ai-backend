from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.email_threads import EmailThreads
from app.domain.interfaces.repositories.email_thread_repository import IEmailThreadRepository


class EmailThreadRepository(IEmailThreadRepository):
    """Repository for email threads."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        query = select(EmailThreads).where(
            EmailThreads.user_id == user_id,
            EmailThreads.assistant_profile_id == assistant_id
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
