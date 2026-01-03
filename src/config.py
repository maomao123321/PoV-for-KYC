from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    fireworks_api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        # Try Streamlit secrets first (for cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and "FIREWORKS_API_KEY" in st.secrets:
                return cls(fireworks_api_key=st.secrets["FIREWORKS_API_KEY"])
        except:
            pass
        
        # Fallback to .env file
        return cls()

