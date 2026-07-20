from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL_NAME", "MODEL_NAME"),
    )
    MISTRAL_API_KEY: str
    MISTRAL_MODEL_NAME: str = "mistral-small-latest"
    LLM_TEMPERATURE: float = 0.0
    LLM_REQUEST_TIMEOUT: int = 60
    LLM_PROVIDER_MAX_RETRIES: int = Field(
        default=1,
        validation_alias=AliasChoices("LLM_PROVIDER_MAX_RETRIES", "LLM_MAX_RETRIES"),
    )

   #Agent operations
    MAX_QA_ITERATIONS: int = 3
    MIN_TASKS: int = 4
    MAX_TASKS: int = 8

    # Storage
    OUTPUT_DIR: str = "output"

    # Agent
    APP_NAME: str = "Autonomous Document Agent"
    APP_VERSION: str = "2.0.0"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

