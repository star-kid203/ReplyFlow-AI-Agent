# FILE: backend/app/core/config.py
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "ReplyFlow API"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # Hackathon Resilience Flag
    SAMPLE_MODE: bool = False

    # Model Provider & Power Layer (NVIDIA & Meterless)
    MODEL_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    MODEL_API_KEY: str = ""
    NEMOTRON_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    METERLESS_BASE_URL: str = "http://127.0.0.1:8088/v1"
    METERLESS_API_KEY: str = ""
    METERLESS_RUNTIME_TOKEN: str = ""
    NVIDIA_API_KEY: str = ""
    LLM_PROVIDER: str = "meterless"

    # Zetaris Data Fabric Layer
    ZETARIS_HOST: str = "localhost"
    ZETARIS_PORT: int = 10000
    ZETARIS_USER: str = "admin@zetaris.com"
    ZETARIS_API_KEY: str = ""
    ZETARIS_REST_URL: str = "http://localhost:8888/api/v1.0"
    ZETARIS_BASE_URL: str = "http://localhost:3000"
    ZETARIS_ORG_ID: int = 1

    # Optional Fallback Model Provider
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"

    # Social Connectors
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    META_VERIFY_TOKEN: str = "replyflow_meta_token_secret"

    # Database (Docker port 5433)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "replyflow"
    POSTGRES_PASSWORD: str = "replyflow_secret"
    POSTGRES_DB: str = "replyflow_db"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()