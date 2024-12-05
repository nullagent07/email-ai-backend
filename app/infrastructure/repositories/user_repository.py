from app.domain.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class UserRepository:
    """Репозиторий для работы с таблицей пользователей."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def add_user(self, user_data: dict) -> User:
        """Добавляет нового пользователя в базу данных."""
        async with self.db_session.begin():
            new_user = User(**user_data)
            self.db_session.add(new_user)
            await self.db_session.commit()
            return new_user

    async def get_user_by_email(self, email: str) -> User:
        """Получает пользователя по email."""
        async with self.db_session.begin():
            result = await self.db_session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
