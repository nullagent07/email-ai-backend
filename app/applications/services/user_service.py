from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.models.users import Users
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.domain.interfaces.services.user_service_interface import IUserService

class UserService(IUserService): 
    """Сервис для работы с пользователями."""

    def __init__(self, db_session: AsyncSession):
        self.user_repository : IUserRepository = UserRepository(db_session=db_session)

    async def create_user(self, user_data: dict) -> Users:
        """Создает нового пользователя."""
        return await self.user_repository.add_user(user_data)

    async def find_user_by_email(self, email: str) -> Users:
        """Находит пользователя по email."""
        # Логика поиска пользователя по email может быть добавлена здесь
        print("Поиск пользователя по email:", email)
        return await self.user_repository.get_user_by_email(email)

    async def find_user_by_id(self, user_id: str) -> Users:
        """Находит пользователя по ID."""
        return await self.user_repository.get_user_by_id(user_id)
