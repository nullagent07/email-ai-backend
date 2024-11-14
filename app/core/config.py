import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from typing import List, Optional
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

    google_basic_scope: list[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    google_extended_scope: list[str] = google_basic_scope + [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify"
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

    # OpenAI settings
    openai_api_key: str = "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"
    openai_base_assistant_id: str = "asst_cYTPINH01O8gjYMjjewn0yOg" # ID предварительно созданного базового ассистента

    google_project_id: str = "effective-reach-425812-u0"
    google_topic_id: str = "l6E-5+QaFnBk-i"
    google_service_account: str = "email-assistant@effective-reach-425812-u0.iam.gserviceaccount.com"

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")

@lru_cache()
def get_app_settings() -> Settings:
    return Settings()

def get_settings_no_cache() -> Settings:
    return Settings()

settings = get_app_settings()
