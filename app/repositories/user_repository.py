from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from uuid import UUID

class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def get_user_by_id(self, user_id: UUID) -> User:
        """Получает пользователя по идентификатору."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User:
        """Получает пользователя по email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        """Создает нового пользователя."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user: User) -> User:
        """Обновляет данные пользователя."""
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        """Удаляет пользователя по идентификатору."""
        user = await self.get_user_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit() 