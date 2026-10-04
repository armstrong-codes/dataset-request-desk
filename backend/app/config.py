from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./desk.db"
    jwt_secret: str = "development-secret-change-me-please-use-32-bytes-minimum"
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
