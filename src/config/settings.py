import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from enum import StrEnum


class AppEnv(StrEnum):
    DEV = "dev"
    PROD = "prod"

_app_env = os.getenv("APP_ENV")

if not _app_env:
    os.environ["APP_ENV"] = AppEnv.DEV.value
    _app_env = AppEnv.DEV.value

_app_env = _app_env.strip()

if _app_env not in (item.value for item in AppEnv):
    raise ValueError(f"APP_ENV is incorrect")

# 从当前模块往上找到 src，和 src 同级别，.env 文件和 src 目录同级
_project_root = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_env: str
    app_id: str = Field(validation_alias="APP_ID")
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")

    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")
    log_handlers: list[str] = Field(default=["console"], validation_alias="LOG_HANDLERS")
    log_format_type: str = Field(default="text", validation_alias="LOG_FORMAT_TYPE")
    log_file: str = Field(default="logs/app.log", validation_alias="LOG_FILE")

    openapi_url: str = Field(default="/openapi.json", validation_alias="OPENAPI_URL")

    cors_allow_origins: list[str] = Field(default=[], validation_alias="CORS_ALLOW_ORIGINS")
    cors_allow_credentials: bool = Field(default=False, validation_alias="CORS_ALLOW_CREDENTIALS")

    openai_provider: str = Field(validation_alias="OPENAI_PROVIDER")
    openai_base_url: str = Field(validation_alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(validation_alias="OPENAI_MODEL")
    openai_temperature: float = Field(
        default=0.7, validation_alias="OPENAI_TEMPERATURE"
    )

    postgres_memory_conn_str: str = Field(validation_alias="POSTGRES_MEMORY_CONN_STR")

    model_config = SettingsConfigDict(
        env_file=[_project_root / ".env", _project_root / f".env.{_app_env}"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings(app_env=_app_env) # type: ignore[call-issue]


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
