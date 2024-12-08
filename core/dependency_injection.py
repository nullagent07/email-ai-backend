from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from authlib.integrations.starlette_client import OAuth

from core.settings import get_app_settings

from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.services.oauth_service import IOAuthService

from app.applications.services.user_service import UserService
from app.applications.services.oauth_service import OAuthService
from app.applications.orcestrators.auth_orchestrator import AuthOrchestrator
from app.applications.services.auth.factory import AuthServiceFactory

from app.domain.interfaces.services.auth_service import IAuthenticationService

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
) -> IAuthenticationService:
    """Получение сервиса аутентификации для указанного провайдера."""
    factory = AuthServiceFactory(google_oauth_client)
    return factory.create_service(provider)

async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Возвращает экземпляр UserService."""
    return UserService(db_session=db)

async def get_oauth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> OAuthService:
    """Возвращает экземпляр OAuthService."""
    return OAuthService(db_session=db)

def get_auth_orchestrator(
    user_service: IUserService = Depends(get_user_service),
    oauth_service: IOAuthService = Depends(get_oauth_service),
    auth_service: IAuthenticationService = Depends(get_auth_service)
) -> AuthOrchestrator:
    return AuthOrchestrator(user_service, oauth_service, auth_service)

# Типизированные зависимости
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
AuthServiceDependency = Annotated[IAuthenticationService, Depends(get_auth_service)]
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
OAuthServiceDependency = Annotated[OAuthService, Depends(get_oauth_service)]
AuthOrchestratorDependency = Annotated[AuthOrchestrator, Depends(get_auth_orchestrator)]