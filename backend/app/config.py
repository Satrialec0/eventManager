from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://eventmanager:eventmanager@127.0.0.1:5432/eventmanager"

    # Marketplace keys (optional until docs/compliance-matrix.md + data-contract.md allow HTTP)
    seatgeek_client_id: str | None = None
    seatgeek_client_secret: str | None = None


settings = Settings()
