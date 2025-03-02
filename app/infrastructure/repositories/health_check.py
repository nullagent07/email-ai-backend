from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.schemas.liveness import LivenessReadinessSchema, LivenessReadinessStatus


class HealthCheckRepository:
    """Репозиторий для проверки состояния базы данных."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def check_database(self) -> LivenessReadinessSchema:
        """Проверяет подключение к базе данных."""
        try:
            # Выполняем простой SELECT 1 для проверки соединения
            await self._session.execute(text("SELECT 1"))
            return LivenessReadinessSchema(status=LivenessReadinessStatus.READY)
        except Exception:
            return LivenessReadinessSchema(status=LivenessReadinessStatus.ERROR)