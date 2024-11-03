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
    # google_scope: list[str] = [
    #     "https://www.googleapis.com/auth/userinfo.profile",
    #     "https://www.googleapis.com/auth/userinfo.email",
    #     "https://www.googleapis.com/auth/gmail.readonly",
    #     "https://www.googleapis.com/auth/gmail.send",
    # ]

    google_basic_scope: list[str] = [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    google_extended_scope: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]


    api_prefix: str = "/api"
    docs_url: str = "/api/docs"
    openapi_url: str = "/api/openapi.json"
    environment: str = "development"
    allowed_hosts: List[str] = ["http://localhost:3000"]    
    access_token_expire_minutes: int = 30
    pool_size: int = 10  # добавьте значение по умолчанию
    secret_key: str
    algorithm: str

    frontend_url: str = "http://localhost:3000"  # URL вашего фронтенда
    cookie_domain: str = "localhost:3000 "  # Домен для кук

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")

@lru_cache()
def get_app_settings() -> Settings:
    return Settings()

def get_settings_no_cache() -> Settings:
    return Settings()

settings = get_app_settings()
