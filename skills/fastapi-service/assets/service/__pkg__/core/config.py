"""설정. 값은 환경변수(.env)에서만 온다. 코드에 시크릿을 두지 않는다."""
from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    app_name: str = "{{service_title}}"
    env: str = "local"
    log_level: str = "INFO"

    # LLM 게이트웨이(LiteLLM). 벤더 SDK 키를 앱에 두지 않는다.
    llm_base_url: str = "http://localhost:4000"
    llm_api_key: SecretStr = SecretStr("")
    llm_default_model: str = "gpt-4o"
    request_timeout_s: float = 30.0

    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
