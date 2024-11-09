# app/services/auth_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.models.user import User
from app.models.oauth_credentials import OAuthCredentials
from app.schemas.oauth_credentials_schema import OAuthCredentialsCreate
from app.core.security import create_access_token, hash_password
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.db = db

    async def register_user(self, name: str, email: str, password: str) -> User:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Хэшируем пароль
        hashed_password = hash_password(password)

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

    # async def authenticate_oauth_user(self, token_data: dict):
    #     # Извлекаем информацию о пользователе из token_data
    #     email = token_data.get("email")
    #     provider = "google"
    #     access_token = token_data.get("access_token")
    #     refresh_token = token_data.get("refresh_token")
    #     expires_in = token_data.get("expires_in")
    #     name = token_data.get("name")

    #     # Проверяем, существует ли пользователь
    #     user = await self.user_repository.get_user_by_email(email)
    #     is_new_user = False

    #     if not user:
    #         # Создаем нового пользователя без пароля
    #         new_user = User(
    #             name=name,
    #             email=email,
    #             is_subscription_active=False  # По умолчанию
    #         )
    #         user = await self.user_repository.create_user(new_user)
    #         is_new_user = True

    #     # Обновляем или создаем OAuthCredentials
    #     oauth_credentials = await self.oauth_repo.get_by_user_id_and_provider(user.id, provider)
    #     if not oauth_credentials:
    #         new_credentials = OAuthCredentials(
    #             user_id=user.id,
    #             provider=provider,
    #             access_token=access_token,
    #             refresh_token=refresh_token,
    #             expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
    #             email=email
    #         )
    #         await self.oauth_repo.create(new_credentials)
    #     else:
    #         # Обновляем существующие учетные данные
    #         oauth_credentials.access_token = access_token
    #         oauth_credentials.refresh_token = refresh_token
    #         oauth_credentials.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    #         await self.oauth_repo.update(oauth_credentials)

    #     # Создаем JWT access_token
    #     token_expires = timedelta(minutes=30)  # Или используйте настройки из конфигурации
    #     token = create_access_token(data={"sub": str(user.id)}, expires_delta=token_expires)

    #     return token, is_new_user

    async def set_password(self, user_id: int, password: str) -> bool:
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            return False
        # Хэшируем пароль
        hashed_password = hash_password(password)
        user.password_hash = hashed_password
        await self.user_repository.update_user(user)
        return True

    async def get_user_by_id(self, user_id: int) -> User:
        return await self.user_repository.get_user_by_id(user_id)
