from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Get the root directory of the project
root_dir = Path(__file__).parent.parent

class BaseAppSettings(BaseSettings):
    title: str = "Email Assistant"
    version: str = "0.1.0"
    summary: str = ""
    description: str = ""

    debug: bool = False

    pg_host: str = os.getenv("PG_HOST", "localhost")
    pg_port: str = os.getenv("PG_PORT", "5432")
    pg_database: str = os.getenv("PG_DATABASE", "health_tracker")
    pg_username: str = os.getenv("PG_USERNAME", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "example")
    pool_size: int = 20

    allowed_hosts: list[str] | None = ["localhost"]


    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        extra="allow"  # Разрешаем дополнительные поля
    )
