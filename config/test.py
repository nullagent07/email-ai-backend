from .base import BaseAppSettings

class TestSettings(BaseAppSettings):
    debug: bool = True
    log_level: str = "DEBUG"
