from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from authlib.integrations.starlette_client import OAuth

from app.applications.services.auth.interfaces import AuthenticationService
from core.settings import get_app_settings

app_settings = get_app_settings()

# Создаем глобальный экземпляр OAuth
oauth = OAuth()

# Регистрируем Google OAuth клиент
google_oauth_client = oauth.register(
    name='google',
    client_id=app_settings.google_client_id,
    client_secret=app_settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'token_endpoint_auth_method': 'client_secret_post'
    }
)

# Формируем строку подключения к PostgreSQL
pg_connection_string = (
    f"postgresql+asyncpg://{app_settings.pg_username}:{app_settings.pg_password}@"
    f"{app_settings.pg_host}:{app_settings.pg_port}/{app_settings.pg_database}"
)

# Создаем асинхронный движок SQLAlchemy
async_engine = create_async_engine(
    pg_connection_string,
    pool_pre_ping=True,
    pool_size=app_settings.pool_size,
)

# Создаем фабрику сессий
async_session = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии с базой данных."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

def get_auth_service(
    provider: Annotated[str, Path()]
) -> AuthenticationService:
    """Получение сервиса аутентификации для указанного провайдера."""
    # Импортируем здесь, чтобы избежать циклических зависимостей
    from app.applications.services.auth.factory import AuthServiceFactory
    factory = AuthServiceFactory()
    return factory.create_service(provider)

# Типизированные зависимости
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
AuthService = Annotated[AuthenticationService, Depends(get_auth_service)]