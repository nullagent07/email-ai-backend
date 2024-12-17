from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.models.gmail_account import GmailAccount


class IGmailAccountRepository(ABC):
    """Интерфейс для GmailAccountRepository."""

    @abstractmethod
    async def create_account(
        self, oauth_credentials_id: UUID, user_id: UUID, watch_data: Optional[dict] = None
    ) -> GmailAccount:
        """Создает новый аккаунт Gmail в базе данных.

        Args:
            oauth_credentials_id: ID OAuth учетных данных
            user_id: ID пользователя
            watch_data: Опциональные данные о watch (history_id, expiration, topic_name)

        Returns:
            Созданный GmailAccount
        """
        pass

    @abstractmethod
    async def get_by_oauth_credentials_id(self, oauth_credentials_id: UUID) -> Optional[GmailAccount]:
        """Получает аккаунт Gmail по ID OAuth учетных данных."""
        pass

    @abstractmethod
    async def update_watch_data(
        self,
        account_id: UUID,
        history_id: str,
        expiration: datetime,
        topic_name: str,
    ) -> Optional[GmailAccount]:
        """Обновляет данные о watch для аккаунта Gmail.

        Args:
            account_id: ID аккаунта Gmail
            history_id: ID истории
            expiration: Время истечения watch
            topic_name: Имя топика Pub/Sub

        Returns:
            Обновленный GmailAccount или None если аккаунт не найден
        """
        pass

    @abstractmethod
    async def remove_watch_data(self, account_id: UUID) -> Optional[GmailAccount]:
        """Удаляет данные о watch для аккаунта Gmail.

        Args:
            account_id: ID аккаунта Gmail

        Returns:
            Обновленный GmailAccount или None если аккаунт не найден
        """
        pass
