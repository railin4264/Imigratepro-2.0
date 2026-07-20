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
        # default, anyone can forge a valid session for any user.
        logger.warning(
            "SECURITY WARNING: SECRET_KEY is still the default value. "
            "Set a unique SECRET_KEY in backend/.env before exposing this server to real traffic."
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
