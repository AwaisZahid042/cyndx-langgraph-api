from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # app
    app_name: str = "Cyndx LangGraph API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # server
    host: str = "0.0.0.0"
    port: int = 8080

    # llm defaults
    default_model: str = "gpt-4o-mini"
    default_temperature: float = 0.7

    # provider keys (need at least one)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # tools
    tavily_api_key: Optional[str] = None

    # rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window: str = "1 minute"

    # auth
    api_key_enabled: bool = False
    api_keys: str = ""

    # otel
    otel_enabled: bool = False
    otel_service_name: str = "cyndx-langgraph-api"
    otel_exporter_endpoint: Optional[str] = None

    @property
    def api_keys_list(self) -> list[str]:
        if not self.api_keys:
            return []
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
