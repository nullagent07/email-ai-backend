from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.repositories.gmail_account_repository import IGmailAccountRepository
from app.domain.interfaces.services.gmail_account_service import IGmailAccountService
from app.domain.models.gmail_account import GmailAccount
from app.infrastructure.repositories.gmail_account_repository import GmailAccountRepository


class GmailAccountService(IGmailAccountService):
    """Сервис для работы с аккаунтами Gmail."""

    def __init__(self, db_session: AsyncSession):
        self.gmail_account_repository: IGmailAccountRepository = GmailAccountRepository(
            db_session=db_session
        )

    async def create_account(
        self,
        oauth_credentials_id: UUID,
        user_id: UUID,
        history_id: Optional[str] = None,
        expiration: Optional[datetime] = None,
        topic_name: Optional[str] = None,
    ) -> GmailAccount:
        """Создает новый аккаунт Gmail."""
        watch_data = None
        if history_id and expiration and topic_name:
            watch_data = {
                "history_id": history_id,
                "expiration": expiration,
                "topic_name": topic_name,
            }
        return await self.gmail_account_repository.create_account(
            oauth_credentials_id=oauth_credentials_id,
            user_id=user_id,
            watch_data=watch_data,
        )

    async def get_by_user_id(self, user_id: UUID) -> Optional[GmailAccount]:
        """Get Gmail account by user ID."""
        return await self.gmail_account_repository.get_by_user_id(user_id)

    async def get_account(self, oauth_credentials_id: UUID) -> Optional[GmailAccount]:
        """Get Gmail account by OAuth credentials ID."""
        return await self.gmail_account_repository.get_by_oauth_credentials(oauth_credentials_id)

    async def get_by_oauth_credentials(self, oauth_credentials_id: UUID) -> Optional[GmailAccount]:
        """Get Gmail account by OAuth credentials ID."""
        return await self.get_account(oauth_credentials_id)

    async def setup_watch(
        self,
        account_id: UUID,
        history_id: str,
        expiration: datetime,
        topic_name: str,
    ) -> Optional[GmailAccount]:
        """Устанавливает watch для аккаунта Gmail."""
        return await self.gmail_account_repository.update_watch_data(
            account_id=account_id,
            history_id=history_id,
            expiration=expiration,
            topic_name=topic_name,
        )

    async def remove_watch(self, account_id: UUID) -> Optional[GmailAccount]:
        """Удаляет watch для аккаунта Gmail."""
        return await self.gmail_account_repository.remove_watch_data(account_id)

    async def update_history_id(self, account_id: UUID, history_id: str) -> Optional[GmailAccount]:
        """
        Обновляет history_id для аккаунта Gmail.

        Args:
            account_id: ID аккаунта Gmail
            history_id: Новый history_id

        Returns:
            Обновленный аккаунт Gmail или None, если аккаунт не найден
        """
        return await self.gmail_account_repository.update_history_id(account_id, history_id)
