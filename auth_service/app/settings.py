import os
from typing import List, Literal

from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings

DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(DOTENV_PATH)


class Settings(BaseSettings):
    environment: Literal["development", "test", "staging", "production"] = "development"

    app_name: str = "Auth Service"
    debug: bool = False
    api_v1_str: str = "/api/v1"

    database_url: str = Field(..., description="PostgreSQL async URL")
    test_database_url: str = Field(..., description="PostgreSQL async URL for tests")
    sync_database_url: str = ""

    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    jwt_secret_key: SecretStr = Field(..., description="Secret key for access tokens")
    jwt_refresh_secret_key: SecretStr = Field(
        ..., description="Secret key for refresh tokens"
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    redis_url: SecretStr = Field(
        default=SecretStr("redis://localhost:6379"),
        description="URL подключения к Redis",
    )

    log_level: str = "INFO"
    log_json_format: bool = False

    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]
    rate_limit_default: str = "5/minute"
    rate_limit_storage: str = "redis"

    mfa_totp_issuer: str = "OnlineCinema Auth"

    @field_validator("database_url", mode="after")
    def check_database_url(cls, v, info):
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "database_url должен начинаться с postgresql+asyncpg:// или sqlite+aiosqlite://"
            )
        info.data["sync_database_url"] = v.replace("+asyncpg", "")
        return v

    @field_validator("jwt_secret_key", "jwt_refresh_secret_key", mode="after")
    def check_jwt_secrets(cls, v: SecretStr, info):
        if len(v.get_secret_value()) < 16:
            raise ValueError(
                f"{info.field_name} должен быть длиной не менее 16 символов"
            )
        return v

    @field_validator("redis_url", mode="after")
    def parse_redis_url(cls, v: SecretStr):
        url = v.get_secret_value()
        if not url.startswith("redis://"):
            raise ValueError("redis_url должен начинаться с redis://")
        return v


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump(exclude={"jwt_secret_key", "jwt_refresh_secret_key"}))