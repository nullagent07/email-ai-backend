from .base import BaseAppSettings

class ProductionSettings(BaseAppSettings):
    debug: bool = False
    database_url: str = "postgresql://user:password@prod-db"
    log_level: str = "ERROR"
