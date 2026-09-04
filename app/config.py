from pydantic import SecretStr
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
    llm_max_retries: int | None = None
    llm_timeout_seconds: float | None = None


settings = Settings()
