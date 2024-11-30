from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.applications.services.health_check import HealthCheckService
from app.presentation.schemas.liveness import LivenessReadinessSchema
from core.dependency_injection import DatabaseSession

router = APIRouter(prefix="/health", tags=["Health Check"])


@router.get("/readiness", response_model=LivenessReadinessSchema)
async def check_readiness(session: DatabaseSession) -> LivenessReadinessSchema:
    """
    Проверяет готовность приложения к работе.
    
    Проверяет:
    - Подключение к базе данных
    """
    service = HealthCheckService(session)
    return await service.check_health()


@router.get("/liveness", response_model=LivenessReadinessSchema)
async def check_liveness(session: DatabaseSession) -> LivenessReadinessSchema:
    """
    Проверяет, что приложение запущено и отвечает.
    """
    service = HealthCheckService(session)
    return await service.check_liveness()