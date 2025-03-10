from typing import Optional
from uuid import UUID

from app.domain.models.users import Users
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.interfaces.repositories.user_repository import IUserRepository
from fastapi import HTTPException

class UserRepository(IUserRepository):
    """Репозиторий для работы с таблицей пользователей."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def add_user(self, user_data: dict) -> Users:
        """Добавляет нового пользователя в базу данных."""
        # async with self.db_session.begin():
        new_user = Users(**user_data)
        self.db_session.add(new_user)
        await self.db_session.commit()
        return new_user

    async def get_user_by_email(self, email: str) -> Optional[Users]:
        """Получает пользователя по email."""
        # async with self.db_session.begin():
        result = await self.db_session.execute(
                select(Users).where(Users.email == email)
            )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[Users]:
        """Получает пользователя по ID."""
        result = await self.db_session.execute(select(Users).where(Users.id == user_id))
        return result.scalar_one_or_none()
