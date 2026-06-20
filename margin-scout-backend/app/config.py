# margin-scout-backend/app/config.py
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "MarginScout SaaS"
    DATABASE_URL: str = "sqlite:///./test.db"
    JWT_SECRET_KEY: str = "fallback_secret_key"
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
    
    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TIMEZONE: str = "UTC"
    
    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_broker_url(cls, v, info):
        # Railway等でREDIS_URLが設定されている場合はそれを使う
        redis_url = info.data.get("REDIS_URL")
        if redis_url:
            return redis_url
        return v

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_result_backend(cls, v, info):
        redis_url = info.data.get("REDIS_URL")
        if redis_url:
            return redis_url
        return v

    # eBay API設定（OAuth 2.0）
    EBAY_ENV: str = "live"
    EBAY_CLIENT_ID: str | None = None
    EBAY_CLIENT_SECRET: str | None = None
    EBAY_REDIRECT_URI: str = "http://localhost:8080/callback"
    EBAY_REFRESH_TOKEN: str | None = None
    EBAY_REQUEST_TIMEOUT: int = 30
    EBAY_MAX_RETRIES: int = 3
    EBAY_RETRY_BACKOFF_FACTOR: float = 2.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
