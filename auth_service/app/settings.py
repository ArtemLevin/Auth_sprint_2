import os
from typing import List, Literal

from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings

DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(DOTENV_PATH)


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"

    APP_NAME: str = "Auth Service"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = Field(..., description="PostgreSQL async URL")
    TEST_DATABASE_URL: str = Field(..., description="PostgreSQL async URL for tests")
    SYNC_DATABASE_URL: str = ""

    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    JWT_SECRET_KEY: SecretStr = Field(..., description="Secret key for access tokens")
    JWT_REFRESH_SECRET_KEY: SecretStr = Field(
        ..., description="Secret key for refresh tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: SecretStr = Field(
        default=SecretStr("redis://localhost:6379"),
        description="URL подключения к Redis",
    )

    LOG_LEVEL: str = "INFO"
    LOG_JSON_FORMAT: bool = False

    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    RATE_LIMIT_DEFAULT: str = "5/minute"
    RATE_LIMIT_STORAGE: str = "redis"

    MFA_TOTP_ISSUER: str = "OnlineCinema Auth"

    @field_validator("DATABASE_URL", mode="after")
    def check_database_url(cls, v, info):
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL должен начинаться с postgresql+asyncpg:// или sqlite+aiosqlite://"
            )
        info.data["SYNC_DATABASE_URL"] = v.replace("+asyncpg", "")
        return v

    @field_validator("JWT_SECRET_KEY", "JWT_REFRESH_SECRET_KEY", mode="after")
    def check_jwt_secrets(cls, v: SecretStr, info):
        if len(v.get_secret_value()) < 16:
            raise ValueError(
                f"{info.field_name} должен быть длиной не менее 16 символов"
            )
        return v

    @field_validator("REDIS_URL", mode="after")
    def parse_redis_url(cls, v: SecretStr):
        url = v.get_secret_value()
        if not url.startswith("redis://"):
            raise ValueError("REDIS_URL должен начинаться с redis://")
        return v


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump(exclude={"JWT_SECRET_KEY", "JWT_REFRESH_SECRET_KEY"}))