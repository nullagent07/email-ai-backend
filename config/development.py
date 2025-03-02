from .base import BaseAppSettings

class DevelopmentSettings(BaseAppSettings):
    debug: bool = True
    log_level: str = "DEBUG"
    cors_origins: list[str] = ["*"]
