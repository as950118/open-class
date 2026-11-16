from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "open-class API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://open_class:change-me-for-local-use@localhost:5432/open_class"
    timezone: str = "Asia/Seoul"
    jwt_secret_key: str = "local-development-only-change-before-deploy"
    jwt_expiration_hours: int = Field(default=12, ge=1, le=168)
    seed_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters")
        if self.app_env != "development" and self.jwt_secret_key == "local-development-only-change-before-deploy":
            raise ValueError("JWT_SECRET_KEY must be changed outside development")
        return self


settings = Settings()
