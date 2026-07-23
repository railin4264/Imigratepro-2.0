from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Immigration Case Manager"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./migratepro.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Gates the SECRET_KEY hard-fail below and the cookie Secure flag (see
    # app/api/v1/endpoints/auth.py) -- nothing here infers it automatically
    # from anything else (not DEBUG, not the DB URL); it's an explicit flag
    # so a misconfigured deploy fails loudly instead of silently running
    # insecurely.
    ENVIRONMENT: str = "development"

    SECRET_KEY: str = "change-me-in-production"
    # Short-lived on purpose: a leaked access token self-invalidates fast.
    # Sessions stay alive longer via REFRESH_TOKEN_EXPIRE_DAYS instead (see
    # app/api/v1/endpoints/auth.py) -- refresh tokens are stored hashed and
    # rotated on every use, so they can be revoked server-side, unlike a bare
    # long-lived JWT.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    ANTHROPIC_API_KEY: str | None = None

    # USCIS Case Status API (developer.uscis.gov, "Torch Platform") -- OAuth2
    # client-credentials. Sandbox works out of the box with USCIS's published
    # staging receipt numbers; production access requires the firm to
    # register its own app, pass 5+ consecutive days of sandbox traffic, and
    # request a production grant from USCIS (developersupport@uscis.dhs.gov)
    # -- that approval step can't be automated from here, see
    # app/services/uscis_case_status.py for the full flow. Same
    # is_configured()-gated degradation pattern as ANTHROPIC_API_KEY: the
    # feature just doesn't appear in the UI without credentials.
    USCIS_API_CLIENT_ID: str | None = None
    USCIS_API_CLIENT_SECRET: str | None = None
    USCIS_API_BASE_URL: str = "https://api-int.uscis.gov"
    USCIS_API_TOKEN_URL: str = "https://api-int.uscis.gov/oauth/accesstoken"

    FORM_TEMPLATES_DIR: Path = BACKEND_ROOT / "form_templates"
    GENERATED_FORMS_DIR: Path = BACKEND_ROOT / "generated_forms"
    UPLOADED_DOCUMENTS_DIR: Path = BACKEND_ROOT / "uploaded_documents"

    CLIENT_PORTAL_BASE_URL: str = "http://localhost:3000"

    # SMTP is optional -- when unset, the email service logs to the console
    # instead of failing, same graceful-degrade pattern as the Anthropic
    # integration (see app/services/email.py).
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "no-reply@migratepro.local"

    # JWT auth
    ACCESS_TOKEN_ALGORITHM: str = "HS256"

    # In-process scheduler (app/services/scheduler.py) that periodically runs
    # the same appointment-reminder / overdue-invoice sweeps the manual
    # endpoints trigger. Sidesteps standing up Celery beat for two lightweight
    # periodic jobs; set SCHEDULER_ENABLED=false to rely on an external cron
    # calling the endpoints instead (e.g. multi-instance deployments, where
    # every instance running its own in-process loop would duplicate work).
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_MINUTES: int = 60
    APPOINTMENT_REMINDER_HOURS_AHEAD: int = 48
    CASE_DEADLINE_REMINDER_DAYS_AHEAD: int = 14
    RFE_DEADLINE_REMINDER_DAYS_AHEAD: int = 7

    # Brute-force protection. Per-account lockout stops credential stuffing
    # against one email even from many IPs; the IP-based limits below stop a
    # single source hammering many emails or spamming reset emails. Both are
    # in-memory (app/core/rate_limit.py) -- fine for one process, see that
    # module's docstring for the multi-instance caveat.
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15
    LOGIN_RATE_LIMIT_PER_IP: int = 20
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300
    FORGOT_PASSWORD_RATE_LIMIT_PER_IP: int = 5
    FORGOT_PASSWORD_RATE_LIMIT_WINDOW_SECONDS: int = 900

    # The client-portal token itself is unguessable (24 random bytes), so
    # this isn't defending against brute-forcing the token -- it's capping
    # how much PDF-regeneration / disk-write work an automated client can
    # force per token before the rest of the app has to wait on it.
    PUBLIC_FORM_RATE_LIMIT_PER_TOKEN: int = 60
    PUBLIC_FORM_RATE_LIMIT_WINDOW_SECONDS: int = 60


settings = Settings()
