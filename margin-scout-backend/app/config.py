# margin-scout-backend/app/config.py
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "MarginScout SaaS"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = False
    CORS_ORIGINS: str | list[str] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    BROWSERLESS_API_KEY: str = "dummy_key"
    BROWSERLESS_API_URL: str = "https://api.browserless.io/v1"
    BROWSERLESS_TIMEOUT_SEC: int = 30
    BROWSERLESS_MAX_RETRIES: int = 2
    BROWSERLESS_RATE_LIMIT_PER_HOUR: int = 100
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TIMEZONE: str = "UTC"
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
