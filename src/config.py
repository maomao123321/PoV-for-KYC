from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    fireworks_api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()

