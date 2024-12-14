from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.repositories.gmail_account_repository import IGmailAccountRepository
from app.domain.models.gmail_account import GmailAccount


class GmailAccountRepository(IGmailAccountRepository):
    """Репозиторий для работы с таблицей аккаунтов Gmail."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create_account(
        self, oauth_credentials_id: UUID, watch_data: Optional[dict] = None
    ) -> GmailAccount:
        """Создает новый аккаунт Gmail в базе данных."""
        async with self.db_session.begin():
            account_data = {"oauth_credentials_id": oauth_credentials_id}
            if watch_data:
                account_data.update(
                    {
                        "watch_history_id": watch_data.get("history_id"),
                        "watch_expiration": watch_data.get("expiration"),
                        "watch_topic_name": watch_data.get("topic_name"),
                    }
                )

            new_account = GmailAccount(**account_data)
            self.db_session.add(new_account)
            await self.db_session.commit()
            return new_account

    async def get_by_oauth_credentials_id(self, oauth_credentials_id: UUID) -> Optional[GmailAccount]:
        """Получает аккаунт Gmail по ID OAuth учетных данных."""
        async with self.db_session.begin():
            result = await self.db_session.execute(
                select(GmailAccount).where(GmailAccount.oauth_credentials_id == oauth_credentials_id)
            )
            return result.scalar_one_or_none()

    async def update_watch_data(
        self,
        account_id: UUID,
        history_id: str,
        expiration: datetime,
        topic_name: str,
    ) -> Optional[GmailAccount]:
        """Обновляет данные о watch для аккаунта Gmail."""
        async with self.db_session.begin():
            result = await self.db_session.execute(
                update(GmailAccount)
                .where(GmailAccount.id == account_id)
                .values(
                    watch_history_id=history_id,
                    watch_expiration=expiration,
                    watch_topic_name=topic_name,
                )
                .returning(GmailAccount)
            )
            return result.scalar_one_or_none()

    async def remove_watch_data(self, account_id: UUID) -> Optional[GmailAccount]:
        """Удаляет данные о watch для аккаунта Gmail."""
        async with self.db_session.begin():
            result = await self.db_session.execute(
                update(GmailAccount)
                .where(GmailAccount.id == account_id)
                .values(
                    watch_history_id=None,
                    watch_expiration=None,
                    watch_topic_name=None,
                )
                .returning(GmailAccount)
            )
            return result.scalar_one_or_none()
