# app/services/auth_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository

from app.services.token_service import TokenService

from app.models.user import User
from app.models.oauth_credentials import OAuthCredentials
from app.schemas.oauth_credentials_schema import OAuthCredentialsCreate
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.token_service = TokenService()
        self.db = db        

    async def register_user(self, name: str, email: str, password: str) -> User:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Хэшируем пароль
        hashed_password = self.token_service.hash_password(password)

        # Создаем нового пользователя
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            is_subscription_active=False  # По умолчанию
        )

        try:
            user = await self.user_repository.create_user(new_user)
            return user
        except IntegrityError:
            # Обработка ошибки, если пользователь с таким email уже существует
            raise ValueError("User with this email already exists")

    async def set_password(self, user_id: int, password: str) -> bool:
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            return False
        # Хэшируем пароль
        hashed_password = self.token_service.hash_password(password)
        user.password_hash = hashed_password
        await self.user_repository.update_user(user)
        return True
