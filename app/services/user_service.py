# app/services/user_service.py

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
# repositories
from app.repositories.user_repository import UserRepository
# models
from app.models.user import User
# services
from app.services.token_service import TokenService
# other
from typing import Optional
import logging
from passlib.context import CryptContext
from fastapi import Request, Depends
from app.core.dependency import get_db
from uuid import UUID

logger = logging.getLogger(__name__)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
        self.token_service = TokenService()

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'UserService':
        """Фабричный метод для создания экземпляра UserService"""
        return cls(db)

    async def register_user(self, name: str, email: str, is_subscription_active: bool = False, password: str = None) -> User:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError("User already exists")

        # Хэшируем пароль
        password_hash = pwd_context.hash(password) if password else None

        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            is_subscription_active=is_subscription_active
        )
        return await self.user_repository.create_user(new_user)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.user_repository.get_user_by_email(email)
        if user and pwd_context.verify(password, user.password_hash):
            return user
        return None

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.user_repository.get_user_by_id(user_id)

    async def get_current_user(self, request: Request) -> Optional[User]:
        # Получаем токен из куков
        access_token_cookie = request.cookies.get("access_token")
        logger.info(f"Got access token from cookie: {access_token_cookie}")
        
        if not access_token_cookie:
            logger.warning("No access token in cookies")
            return None
            
        if not access_token_cookie.startswith("Bearer "):
            logger.warning("Token doesn't start with Bearer")
            return None
            
        token = access_token_cookie.split(" ")[1]
        logger.info("Successfully extracted token")

        # Проверяем токен и получаем пользователя
        try:
            payload = self.token_service.verify_token(token)
            if not payload:
                logger.warning("Invalid token payload")
                return None
                
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No user_id in token payload")
                return None

            user = await self.user_repository.get_user_by_id(UUID(user_id))
            logger.info(f"Found user: {user.email if user else None}")
            return user
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            return await self.user_repository.get_user_by_id(UUID(user_id))
        except Exception:
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email"""
        return await self.user_repository.get_user_by_email(email)