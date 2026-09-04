from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    database_url: str = "sqlite:///./app.db"
    llm_max_retries: int = Field(default=3, ge=0)
    llm_timeout_seconds: float = Field(default=30, gt=0)


settings = Settings()
