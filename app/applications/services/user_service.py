from typing import Optional
from uuid import UUID

from app.domain.models.users import Users
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.domain.interfaces.services.user_service import IUserService
from fastapi import HTTPException
from app.infrastructure.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

class UserService(IUserService): 
    """Сервис для работы с пользователями."""

    def __init__(self, db_session: AsyncSession):
        self._repository : IUserRepository = UserRepository(
            db_session=db_session
            )

    async def create_user(self, user_data: dict) -> Users:
        """Создает нового пользователя."""
        return await self._repository.add_user(user_data)

    async def find_user_by_email(self, email: str) -> Optional[Users]:
        """Находит пользователя по email."""
        # Логика поиска пользователя по email может быть добавлена здесь
        print("Поиск пользователя по email:", email)
        return await self._repository.get_user_by_email(email)

    async def find_user_by_id(self, user_id: UUID) -> Optional[Users]:
        """Находит пользователя по ID."""
        return await self._repository.get_user_by_id(user_id)
