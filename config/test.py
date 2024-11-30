from .base import BaseAppSettings

class TestSettings(BaseAppSettings):
    debug: bool = True
    database_url: str = "sqlite:///./test.db"
    log_level: str = "DEBUG"
