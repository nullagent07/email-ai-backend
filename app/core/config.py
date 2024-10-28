import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from typing import List
import os

load_dotenv()

class Settings(BaseSettings):
    # Существующие настройки
    pg_username: str
    pg_password: str
    pg_host: str
    pg_port: int
    pg_database: str

    # Google OAuth настройки
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    api_prefix: str = "/api"
    docs_url: str = "/api/docs"
    openapi_url: str = "/api/openapi.json"
    environment: str = "development"
    allowed_hosts: List[str] = ["*"]

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")

@lru_cache()
def get_app_settings() -> Settings:
    return Settings()

def get_settings_no_cache() -> Settings:
    return Settings()
