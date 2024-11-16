# app/dependencies.py

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_app_settings

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
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения асинхронной сессии БД."""
    async with async_session() as session:
        yield session

# def get_auth_service(
#     db: Annotated[AsyncSession, Depends(get_db)]
# ) -> AuthService:
#     """Возвращает экземпляр AuthService."""
#     return AuthService(db)

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")