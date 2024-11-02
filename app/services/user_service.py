# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user_schema import UserCreate
from typing import Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)

    async def register_user(self, user_create: UserCreate) -> User:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await self.user_repository.get_user_by_email(user_create.email)
        if existing_user:
            raise ValueError("User already exists")

        # Хэшируем пароль
        password_hash = pwd_context.hash(user_create.password)

        new_user = User(
            name=user_create.name,
            email=user_create.email,
            password_hash=password_hash
        )
        return await self.user_repository.create_user(new_user)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.user_repository.get_user_by_email(email)
        if user and pwd_context.verify(password, user.password_hash):
            return user
        return None

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.user_repository.get_user_by_id(user_id)

    # Добавьте дополнительные асинхронные методы по необходимости

