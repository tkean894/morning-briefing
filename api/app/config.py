from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://localhost/morning_briefs"
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    environment: str = "development"


settings = Settings()
