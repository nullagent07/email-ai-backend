from pydantic_settings import BaseSettings
import os
from pathlib import Path

# Get the root directory of the project
root_dir = Path(__file__).parent.parent

class BaseAppSettings(BaseSettings):
    project_name: str = "FastAPI Project"
    version: str = "1.0.0"
    debug: bool = False
    database_url: str

    class Config:
        env_file = root_dir / ".env"
