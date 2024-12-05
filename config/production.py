from .base import BaseAppSettings

class ProductionSettings(BaseAppSettings):
    debug: bool = False
    log_level: str = "ERROR"
