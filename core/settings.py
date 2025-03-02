import os
from functools import lru_cache
from config.development import DevelopmentSettings
from config.production import ProductionSettings
from config.test import TestSettings

def get_settings():
    env = os.getenv("env", "development").lower()
    match env:
        case "development":
            return DevelopmentSettings()
        case "production":
            return ProductionSettings()
        case "test":
            return TestSettings()
        case _:
            raise ValueError(f"Unknown environment: {env}")


@lru_cache()
def get_app_settings():
    return get_settings()