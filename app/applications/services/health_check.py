from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.health_check import HealthCheckRepository
from app.presentation.schemas.liveness import LivenessReadinessSchema


class HealthCheckService:
    """Сервис для проверки состояния приложения."""

    def __init__(self, session: AsyncSession):
        self._repository = HealthCheckRepository(session)

    async def check_health(self) -> LivenessReadinessSchema:
        """Проверяет состояние приложения и базы данных."""
        return await self._repository.check_database()

    async def check_liveness(self) -> LivenessReadinessSchema:
        """Проверяет, что приложение запущено и отвечает."""
        # В данном случае, если метод вызван, значит приложение живо
        return LivenessReadinessSchema()