import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services import scheduler

# Uvicorn only configures its own "uvicorn"/"uvicorn.access"/"uvicorn.error"
# loggers -- without this, the "migratepro.*" loggers (email fallback logging,
# scheduler sweeps) have no handler anywhere and silently go nowhere, which
# defeats the whole point of logging instead of failing loudly.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("migratepro.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY == "change-me-in-production":
        # Loud and repeated on purpose: this key signs every access token
        # and verifies every refresh/reset token. Left at the shipped
        # default, anyone can forge a valid session for any user. In
        # production that's not a warning-worthy misconfiguration, it's a
        # refuse-to-start one -- every other environment just gets the loud
        # warning so local dev/CI keeps working without extra setup.
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "Refusing to start: SECRET_KEY is still the default value with ENVIRONMENT=production. "
                "Set a unique SECRET_KEY in backend/.env before exposing this server to real traffic."
            )
        logger.warning(
            "SECURITY WARNING: SECRET_KEY is still the default value. "
            "Set a unique SECRET_KEY in backend/.env before exposing this server to real traffic."
        )

    # Same fail-loud/warn-loud split as SECRET_KEY above: the shipped default
    # is localhost-only, so leaving it in production either breaks the real
    # frontend origin or (if someone "fixes" that by adding a wildcard)
    # silently opens CORS to any origin. Every other environment just warns
    # so local dev/CI keeps working unconfigured.
    if settings.CORS_ORIGINS == ["http://localhost:3000"]:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "Refusing to start: CORS_ORIGINS is still the localhost default with ENVIRONMENT=production. "
                "Set CORS_ORIGINS in backend/.env to the real frontend origin(s) before exposing this server to real traffic."
            )
        logger.warning(
            "SECURITY WARNING: CORS_ORIGINS is still the localhost default. "
            "Set CORS_ORIGINS in backend/.env to the real frontend origin(s) before exposing this server to real traffic."
        )

    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok"}
