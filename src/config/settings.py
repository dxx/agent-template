import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from enum import StrEnum

class AppEnv(StrEnum):
    DEFAULT = "default"
    DEV = "dev"
    PROD = "prod"

APP_ENV = os.getenv("APP_ENV")

if not APP_ENV:
    os.environ["APP_ENV"] = "default"
    APP_ENV = "default"

if APP_ENV not in (item.value for item in AppEnv):
    raise ValueError(f"APP_ENV is incorrect")

env_file = ".env" if os.getenv("APP_ENV") == "default" else f".{os.getenv("APP_ENV")}"

# 从当前模块往上找到 src，和 src 同级别，.env 文件和 src 目录同级
path = Path(__file__).resolve().parent.parent.parent
env_path = path.joinpath(env_file)

class Settings(BaseSettings):
    app_env: str = APP_ENV
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_handlers: list[str] = Field(validation_alias="LOG_HANDLERS")
    log_format_type: str = Field(default="text", validation_alias="LOG_FORMAT_TYPE")
    log_file: str = Field(default="app.log", validation_alias="LOG_FILE")

    openapi_url: str = Field(default="/openapi.json", validation_alias="OPENAPI_URL")

    openai_base_url: str = Field(validation_alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(validation_alias="OPENAI_MODEL")
    openai_temperature: float = Field(
        default=0.7, validation_alias="OPENAI_TEMPERATURE"
    )

    postgres_checkpointer_conn_str: str = Field(validation_alias="POSTGRES_CHECKPOINTER_CONN_STR")

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
