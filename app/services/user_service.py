# app/services/user_service.py

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
# repositories
from app.repositories.user_repository import UserRepository
# models
from app.models.user import User
# schemas
from app.schemas.user_schema import UserCreate
# services
from app.services.token_service import TokenService
from app.services.auth_service import AuthService
# other
from typing import Optional
import logging
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status, Depends
from jose import JWTError
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

    async def get_current_user(self, request: Request) -> Optional[User]:
        # Получаем токен из куков
        access_token_cookie = request.cookies.get("access_token")
        
        if not access_token_cookie or not access_token_cookie.startswith("Bearer "):
            return None
            
        token = access_token_cookie.split(" ")[1]

        # Проверяем токен и получаем пользователя
        try:
            payload = self.token_service.verify_token(token)
            if not payload:
                return None
                
            user_id = payload.get("sub")
            if not user_id:
                return None

            return await self.user_repository.get_user_by_id(UUID(user_id))
        except Exception:
            return None

