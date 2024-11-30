from .base import BaseAppSettings

class DevelopmentSettings(BaseAppSettings):
    debug: bool = True
    database_url: str = "sqlite:///./development.db"
    log_level: str = "DEBUG"
