from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.settings import get_app_settings

app_settings = get_app_settings()

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

# Типизированная зависимость для базы данных
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]