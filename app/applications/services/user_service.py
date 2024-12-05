from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, db_session: AsyncSession):
        self.user_repository = UserRepository(db_session=db_session)

    async def create_user(self, user_data: dict) -> User:
        """Создает нового пользователя."""
        return await self.user_repository.add_user(user_data)

    async def find_user_by_email(self, email: str) -> User:
        """Находит пользователя по email."""
        # Логика поиска пользователя по email может быть добавлена здесь
        print("Поиск пользователя по email:", email)
        return await self.user_repository.get_user_by_email(email)
