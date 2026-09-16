from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://localhost/morning_briefs"
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    environment: str = "development"
    guardian_api_key: str = ""
    nyt_api_key: str = ""
    gemini_api_key: str = ""
    google_tts_credentials_json: str = ""
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_public_url_base: str = ""


settings = Settings()
