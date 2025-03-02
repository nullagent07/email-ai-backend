from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.models.gmail_account import GmailAccount


class IGmailAccountService(ABC):
    """Интерфейс для GmailAccountService."""

    @abstractmethod
    async def create_account(
        self,
        oauth_credentials_id: UUID,
        user_id: UUID,
        history_id: Optional[str] = None,
        expiration: Optional[datetime] = None,
        topic_name: Optional[str] = None,
    ) -> GmailAccount:
        """Создает новый аккаунт Gmail.
        
        Args:
            oauth_credentials_id: ID OAuth учетных данных
            user_id: ID пользователя
            history_id: Опциональный ID истории для watch
            expiration: Опциональное время истечения watch
            topic_name: Опциональное имя топика Pub/Sub для watch

        Returns:
            Созданный GmailAccount
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[GmailAccount]:
        """
        Получает аккаунт Gmail по ID пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[GmailAccount]: Найденный аккаунт Gmail или None
        """
        pass

    @abstractmethod
    async def get_by_oauth_credentials(self, oauth_credentials_id: UUID) -> Optional[GmailAccount]:
        """
        Получает аккаунт Gmail по ID OAuth учетных данных.
        
        Args:
            oauth_credentials_id: ID OAuth учетных данных
            
        Returns:
            Optional[GmailAccount]: Найденный аккаунт Gmail или None
        """
        pass

    @abstractmethod
    async def setup_watch(
        self,
        account_id: UUID,
        history_id: str,
        expiration: datetime,
        topic_name: str,
    ) -> Optional[GmailAccount]:
        """Устанавливает watch для аккаунта Gmail.

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
    async def remove_watch(self, account_id: UUID) -> Optional[GmailAccount]:
        """Удаляет watch для аккаунта Gmail.

        Args:
            account_id: ID аккаунта Gmail

        Returns:
            Обновленный GmailAccount или None если аккаунт не найден
        """
        pass

    @abstractmethod
    async def update_history_id(self, account_id: UUID, history_id: str) -> Optional[GmailAccount]:
        """
        Обновляет history_id для аккаунта Gmail.

        Args:
            account_id: ID аккаунта Gmail
            history_id: Новый history_id

        Returns:
            Обновленный аккаунт Gmail или None, если аккаунт не найден
        """
        pass
