from collections.abc import AsyncGenerator
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Path, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from authlib.integrations.starlette_client import OAuth

from core.settings import get_app_settings

from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.services.oauth_service import IOAuthService
from app.domain.interfaces.orchestrators.assistant_orchestrator import IAssistantOrchestrator
from app.domain.interfaces.repositories.assistant_profiles_repository import IAssistantProfilesRepository
from app.domain.interfaces.services.assistant_profile_service import IAssistantProfileService

from app.applications.services.user_service import UserService
from app.applications.services.oauth_service import OAuthService
from app.applications.orchestrators.auth_orchestrator import AuthOrchestrator
from app.applications.orchestrators.openai.assistant_orchestrator import AssistantOrchestrator
from app.applications.factories.auth_factory import AuthServiceFactory
from app.infrastructure.repositories.assistant_profiles_repository import AssistantProfilesRepository
from app.applications.services.assistant_profile_service import AssistantProfileService

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

async def get_assistant_profiles_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> IAssistantProfilesRepository:
    """Возвращает экземпляр AssistantProfilesRepository."""
    return AssistantProfilesRepository(session=db)

async def get_assistant_profile_service(
    profiles_repository: Annotated[IAssistantProfilesRepository, Depends(get_assistant_profiles_repository)]
) -> IAssistantProfileService:
    """Возвращает экземпляр AssistantProfileService."""
    return AssistantProfileService(profiles_repository=profiles_repository)

async def get_assistant_orchestrator(
    profiles_repository: Annotated[IAssistantProfilesRepository, Depends(get_assistant_profiles_repository)],
    request: Request
) -> IAssistantOrchestrator:
    """Возвращает экземпляр AssistantOrchestrator."""
    orchestrator = AssistantOrchestrator(profiles_repository=profiles_repository)
    
    # Инициализируем OpenAI клиент только если это не GET /api/assistants
    if not (request.method == "GET" and request.url.path == "/api/assistants"):
        await orchestrator.initialize(
            api_key=app_settings.openai_api_key,
            organization=app_settings.openai_organization
        )
    
    return orchestrator

def get_auth_orchestrator(
    user_service: IUserService = Depends(get_user_service),
    oauth_service: IOAuthService = Depends(get_oauth_service),
    auth_service: IAuthenticationService = Depends(get_auth_service)
) -> AuthOrchestrator:
    return AuthOrchestrator(user_service, oauth_service, auth_service)

async def get_current_user_id(
    request: Request,
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)]
) -> UUID:
    """
    Получает ID пользователя из access_token в куках.
    
    Args:
        request: FastAPI Request объект
        oauth_service: Сервис для работы с OAuth
        
    Returns:
        UUID: ID текущего пользователя
        
    Raises:
        HTTPException: Если пользователь не аутентифицирован или токен недействителен
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    credentials = await oauth_service.find_by_access_token(access_token)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return credentials.user_id

# Типизированные зависимости
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
AuthServiceDependency = Annotated[IAuthenticationService, Depends(get_auth_service)]
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
OAuthServiceDependency = Annotated[OAuthService, Depends(get_oauth_service)]
AuthOrchestratorDependency = Annotated[AuthOrchestrator, Depends(get_auth_orchestrator)]
AssistantOrchestratorDependency = Annotated[IAssistantOrchestrator, Depends(get_assistant_orchestrator)]
AssistantProfilesRepositoryDependency = Annotated[IAssistantProfilesRepository, Depends(get_assistant_profiles_repository)]
AssistantProfileServiceDependency = Annotated[IAssistantProfileService, Depends(get_assistant_profile_service)]
CurrentUserDependency = Annotated[UUID, Depends(get_current_user_id)]