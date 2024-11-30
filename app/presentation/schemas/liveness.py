from enum import StrEnum

from pydantic import BaseModel, Field


class LivenessReadinessStatus(StrEnum):
    """Схема Enum для статуса приложения."""

    READY = "ready"
    ALIVE = "alive"
    ERROR = "error"


class LivenessReadinessSchema(BaseModel):
    """Схема статуса приложения и бд."""

    status: LivenessReadinessStatus = Field(
        description="Статус проверки на доступность и читаемость",
        default=LivenessReadinessStatus.READY,
        examples=["ready", "alive", "error"],
    )