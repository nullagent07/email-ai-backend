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

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        extra="allow"  # Разрешаем дополнительные поля
    )
