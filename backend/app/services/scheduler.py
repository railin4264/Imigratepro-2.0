"""A minimal in-process scheduler: one asyncio background task, started from
FastAPI's lifespan, that periodically runs the appointment-reminder,
invoice-overdue, and expired-token-cleanup sweeps. No new dependency (no
APScheduler, no Celery beat) -- Celery/Redis are already in the stack for
future background work, but adding a whole beat scheduler + worker process
for a few lightweight periodic queries would be a lot of moving parts for
what this is. If this ever needs to run across multiple backend instances,
switch SCHEDULER_ENABLED off on all but one, or move to Celery beat so the
jobs are centrally coordinated instead of duplicated per instance."""

import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.reminders import (
    mark_overdue_invoices,
    send_appointment_reminders,
    send_case_deadline_reminders,
    send_rfe_deadline_reminders,
)
from app.services.token_cleanup import cleanup_expired_tokens

logger = logging.getLogger("migratepro.scheduler")

_task: asyncio.Task | None = None


def _run_sweeps_once() -> None:
    db = SessionLocal()
    try:
        reminders = send_appointment_reminders(db)
        overdue = mark_overdue_invoices(db)
        case_deadlines = send_case_deadline_reminders(db)
        rfe_deadlines = send_rfe_deadline_reminders(db)
        cleanup = cleanup_expired_tokens(db)
        if reminders["reminders_sent"] or overdue["marked_overdue"]:
            logger.info("scheduler sweep: %s, %s", reminders, overdue)
        if case_deadlines["reminders_sent"] or rfe_deadlines["reminders_sent"]:
            logger.info("scheduler deadline sweep: %s, %s", case_deadlines, rfe_deadlines)
        if cleanup["refresh_tokens_deleted"] or cleanup["reset_tokens_deleted"]:
            logger.info("scheduler token cleanup: %s", cleanup)
    except Exception:
        logger.exception("scheduled sweep failed")
    finally:
        db.close()


async def _loop() -> None:
    interval_seconds = settings.SCHEDULER_INTERVAL_MINUTES * 60
    while True:
        # Run in a worker thread -- SessionLocal/requests inside are sync.
        await asyncio.to_thread(_run_sweeps_once)
        await asyncio.sleep(interval_seconds)


def start() -> None:
    global _task
    if not settings.SCHEDULER_ENABLED or _task is not None:
        return
    _task = asyncio.get_event_loop().create_task(_loop())
    logger.info("scheduler started (every %s minutes)", settings.SCHEDULER_INTERVAL_MINUTES)


def stop() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
