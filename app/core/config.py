import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    pg_username: str
    pg_password: str
    pg_host: str
    pg_port: int
    pg_database: str

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")

@lru_cache()
def get_app_settings() -> Settings:
    return Settings()

def get_settings_no_cache() -> Settings:
    return Settings()

