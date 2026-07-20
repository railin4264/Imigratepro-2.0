import asyncio

import pytest

from app.main import lifespan, app


def _run_lifespan():
    async def _enter_and_exit():
        async with lifespan(app):
            pass

    asyncio.run(_enter_and_exit())


def test_refuses_to_start_in_production_with_default_secret_key(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SECRET_KEY", "change-me-in-production")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="Refusing to start"):
        _run_lifespan()


def test_starts_with_a_warning_in_development_with_default_secret_key(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SECRET_KEY", "change-me-in-production")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    # Must not raise -- local dev/CI shouldn't be forced to set a real key.
    _run_lifespan()


def test_starts_normally_in_production_with_a_real_secret_key(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SECRET_KEY", "a-real-unique-production-secret")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    _run_lifespan()
