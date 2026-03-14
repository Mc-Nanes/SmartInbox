from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartInbox"
    app_description: str = "Classificação inteligente de emails corporativos"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    max_upload_size_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    allowed_extensions: tuple[str, ...] = (".txt", ".pdf")
    enable_local_ai_fallback: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
