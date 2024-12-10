from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
from typing import List
import secrets

# Get the root directory of the project
root_dir = Path(__file__).parent.parent

class BaseAppSettings(BaseSettings):
    """Базовые настройки приложения."""
    
    # Основные настройки приложения
    title: str = "Email Assistant"
    version: str = "0.1.0"
    summary: str = ""
    description: str = ""

    # Настройки безопасности
    secret_key: str = secrets.token_urlsafe(32)  # Генерируем безопасный ключ
    debug: bool = False

    pg_host: str = os.getenv("PG_HOST", "localhost")
    pg_port: str = os.getenv("PG_PORT", "5432")
    pg_database: str = os.getenv("PG_DATABASE", "postgres")
    pg_username: str = os.getenv("PG_USERNAME", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "example")
    pool_size: int = 20

    allowed_hosts: list[str] | None = ["localhost"]

    # Настройки CORS
    cors_origins: List[str] = ["*"]

    # Google OAuth настройки
    google_client_id: str = "835611854691-tut9ae4v042o4tapcsgflfcvd31j3afh.apps.googleusercontent.com"
    google_client_secret: str = "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"
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"  # Обновлен в соответствии с Google Console

    google_project_id: str = "effective-reach-425812-u0"
    google_topic_id: str = "l6E-5+QaFnBk-i"
    google_service_account: str = "email-assistant@effective-reach-425812-u0.iam.gserviceaccount.com"
    google_pubsub_topic_name: str = "projects/effective-reach-425812-u0/topics/l6E-5+QaFnBk-i"

    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "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")
    openai_organization: str = os.getenv("OPENAI_ORGANIZATION", "")

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        extra="allow"  # Разрешаем дополнительные поля
    )
