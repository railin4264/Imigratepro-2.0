from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Immigration Case Manager"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./migratepro.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    ANTHROPIC_API_KEY: str | None = None

    FORM_TEMPLATES_DIR: Path = BACKEND_ROOT / "form_templates"
    GENERATED_FORMS_DIR: Path = BACKEND_ROOT / "generated_forms"
    UPLOADED_DOCUMENTS_DIR: Path = BACKEND_ROOT / "uploaded_documents"

    CLIENT_PORTAL_BASE_URL: str = "http://localhost:3000"


settings = Settings()
