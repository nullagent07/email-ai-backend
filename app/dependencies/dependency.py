from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_app_settings
from app.services.auth_service import AuthService
from app.repositories.auth_repository import AuthRepository
from jose import JWTError, jwt
from app.models.user import User
# from app.utils.security import verify_access_token
from app.core.security import verify_access_token

settings = get_app_settings()

# Строка подключения к PostgreSQL
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.pg_username}:{settings.pg_password}@"
    f"{settings.pg_host}:{settings.pg_port}/{settings.pg_database}"
)

# Создаем движок для асинхронного подключения
async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.pool_size,
)

# Создаем фабрику сессий
async_session = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения асинхронной сессии БД."""
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AuthService:
    """Возвращает экземпляр AuthService."""
    return AuthService(AuthRepository(db_session=db))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходимо авторизоваться",
        )
    # Убираем префикс "Bearer "
    token = token.replace("Bearer ", "")
    try:
        # Проверяем и декодируем токен
        payload = verify_access_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Не удалось получить идентификатор пользователя",
            )
        # Получаем пользователя из базы данных
        user = await User.get(id=user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
        )

