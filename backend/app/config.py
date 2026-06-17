"""Application configuration loaded from environment variables.

Secrets (DB credentials) should be provided via environment variables that
are themselves sourced from Azure Key Vault in deployed environments.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Retail DataSecOps API"
    environment: str = "dev"
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Auth (JWT). Override JWT_SECRET in deployed environments (sourced from Key Vault).
    jwt_secret: str = "dev-only-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Default seed users created on startup in DEV (username:password:role, comma-separated).
    seed_users: str = "admin:admin123:admin,engineer:engineer123:data_engineer,analyst:analyst123:analyst"

    # Database. Default to a local SQLite file so the project runs out-of-the-box
    # in a single DEV environment. Override DATABASE_URL for Azure SQL.
    #
    # Azure SQL example:
    # mssql+pyodbc://<user>:<password>@<server>.database.windows.net:1433/<db>?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
    database_url: str = "sqlite:///./retail_dev.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
