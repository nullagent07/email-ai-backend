from collections.abc import AsyncGenerator
from typing import Annotated, Optional, cast
from uuid import UUID
from datetime import datetime

from fastapi import Depends, Path, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App

from core.settings import get_app_settings

from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.domain.interfaces.services.oauth_service import IOAuthService
from app.domain.interfaces.orchestrators.assistant_orchestrator import IAssistantOrchestrator
from app.domain.interfaces.repositories.assistant_profiles_repository import IAssistantProfilesRepository
from app.domain.interfaces.services.assistant_profile_service import IAssistantProfileService
from app.domain.interfaces.repositories.email_thread_repository import IEmailThreadRepository
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.interfaces.orchestrators.email_thread_orchestrator import IEmailThreadOrchestrator
from app.domain.interfaces.repositories.gmail_account_repository import IGmailAccountRepository
from app.domain.interfaces.services.gmail_account_service import IGmailAccountService


from app.applications.services.user_service import UserService
from app.infrastructure.repositories.user_repository import UserRepository
from app.applications.services.oauth_service import OAuthService
from app.applications.orchestrators.auth_orchestrator import AuthOrchestrator
from app.applications.orchestrators.openai.assistant_orchestrator import AssistantOrchestrator
from app.applications.factories.auth_factory import AuthServiceFactory
from app.infrastructure.repositories.assistant_profiles_repository import AssistantProfilesRepository
from app.applications.services.assistant_profile_service import AssistantProfileService
from app.infrastructure.repositories.email_thread_repository import EmailThreadRepository
from app.applications.services.email_thread_service import EmailThreadService
from app.applications.orchestrators.openai.email_thread_orchestrator import EmailThreadOrchestrator
from app.infrastructure.repositories.gmail_account_repository import GmailAccountRepository
from app.applications.services.gmail_account_service import GmailAccountService

from app.domain.interfaces.services.auth_service import IAuthenticationService

app_settings = get_app_settings()

# Создаем глобальный экземпляр OAuth
oauth = OAuth()

# Регистрируем Google OAuth клиент
google_oauth_client: StarletteOAuth2App = cast(StarletteOAuth2App, oauth.register(
    name='google',
    client_id=app_settings.google_client_id,
    client_secret=app_settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify',
        'token_endpoint_auth_method': 'client_secret_post'
    }
))

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

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

async def get_user_repository(
    db: DatabaseSession
    ) -> IUserRepository:
    """Возвращает экземпляр UserService."""
    return UserRepository(db)

async def get_assistant_profiles_repository(
    db: DatabaseSession
) -> IAssistantProfilesRepository:
    """Возвращает экземпляр AssistantProfilesRepository."""
    return AssistantProfilesRepository(db)

async def get_email_thread_repository(
    db: DatabaseSession
) -> IEmailThreadRepository:
    """Get email thread repository instance."""
    return EmailThreadRepository(db)

async def get_gmail_account_repository(
    db: DatabaseSession
) -> IGmailAccountRepository:
    """Get Gmail account repository instance."""
    return GmailAccountRepository(db)

# """ ===== Repositories  ==== """
UserRepositoryDependency = Annotated[IUserRepository, Depends(get_user_repository)]
AssistantProfilesRepositoryDependency = Annotated[IAssistantProfilesRepository, Depends(get_assistant_profiles_repository)]
EmailThreadRepositoryDependency = Annotated[IEmailThreadRepository, Depends(get_email_thread_repository)]
GmailAccountRepositoryDependency = Annotated[IGmailAccountRepository, Depends(get_gmail_account_repository)]
# """ ===== Repositories  ==== """

def get_auth_service(
    provider: Annotated[str, Path()]
) -> IAuthenticationService:
    """Получение сервиса аутентификации для указанного провайдера."""
    factory = AuthServiceFactory(google_oauth_client)
    return factory.create_service(provider)

async def get_user_service(
    db: DatabaseSession
) -> IUserService:
    """Возвращает экземпляр UserService."""
    return UserService(db)

async def get_oauth_service(db: DatabaseSession) -> IOAuthService:
    """Возвращает экземпляр OAuthService."""
    return OAuthService(db)

async def get_assistant_profile_service(
    db : DatabaseSession
) -> IAssistantProfileService:
    """Возвращает экземпляр AssistantProfileService."""
    return AssistantProfileService(db)

async def get_email_thread_service(
    user_service: Annotated[IUserService, Depends(get_user_service)]
) -> IEmailThreadService:
    """Get email thread service instance."""
    return EmailThreadService(user_service)

async def get_gmail_account_service(
) -> IGmailAccountService:
    """Get Gmail account service instance."""
    return GmailAccountService(user_service)

# """ ===== Services  ==== """ #
AuthServiceDependency = Annotated[IAuthenticationService, Depends(get_auth_service)]
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
OAuthServiceDependency = Annotated[OAuthService, Depends(get_oauth_service)]
AssistantProfileServiceDependency = Annotated[IAssistantProfileService, Depends(get_assistant_profile_service)]
EmailThreadServiceDependency = Annotated[IEmailThreadService, Depends(get_email_thread_service)]
GmailAccountServiceDependency = Annotated[IGmailAccountService, Depends(get_gmail_account_service)]
# """ ===== Services  ==== """ #

async def get_current_user_id(
    request: Request,
    oauth_service: OAuthServiceDependency
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
    
    current_time = datetime.utcnow()
    if credentials.expires_at <= current_time:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    
    return credentials.user_id

async def get_assistant_orchestrator(
    profiles_repository: Annotated[IAssistantProfilesRepository, Depends(get_assistant_profiles_repository)],
) -> IAssistantOrchestrator:
    """Возвращает экземпляр AssistantOrchestrator."""
    if not app_settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key is not configured"
        )
        
    orchestrator = AssistantOrchestrator(profiles_repository=profiles_repository)
    try:
        await orchestrator.initialize(
            api_key=app_settings.openai_api_key,
            organization=app_settings.openai_organization
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize OpenAI client: {str(e)}"
        )
    
    return orchestrator

def get_auth_orchestrator(
    user_service: UserServiceDependency,
    oauth_service: OAuthServiceDependency,
    auth_service: AuthServiceDependency
) -> AuthOrchestrator:
    return AuthOrchestrator(user_service, oauth_service, auth_service)
    
async def get_email_thread_orchestrator(
    email_thread_service: EmailThreadServiceDependency,
    user_service: UserServiceDependency,
) -> IEmailThreadOrchestrator:
    """Get email thread orchestrator instance."""
    orchestrator = EmailThreadOrchestrator(
        email_thread_service=email_thread_service,
        user_service=user_service,
    )
    
    # Initialize OpenAI services
    await orchestrator.initialize(
        api_key=app_settings.openai_api_key,
        organization=app_settings.openai_organization
    )
    
    return orchestrator


# """ ===== Dependency Injection ==== """ #
CurrentUserDependency = Annotated[UUID, Depends(get_current_user_id)]

AuthOrchestratorDependency = Annotated[AuthOrchestrator, Depends(get_auth_orchestrator)]
AssistantOrchestratorDependency = Annotated[IAssistantOrchestrator, Depends(get_assistant_orchestrator)]
EmailThreadOrchestratorDependency = Annotated[IEmailThreadOrchestrator, Depends(get_email_thread_orchestrator)]
