"""Outbound email for reminders and notifications. Requires SMTP_HOST (and
usually SMTP_USERNAME/SMTP_PASSWORD) to be set in backend/.env -- if it isn't,
is_configured() is False and send() logs the message instead of raising, so
the rest of the app (reminders, invoices) keeps working without real SMTP
credentials configured. Same graceful-degrade pattern as document_ai.py."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models.case import Case, ParticipantRole

logger = logging.getLogger("migratepro.email")


def is_configured() -> bool:
    return bool(settings.SMTP_HOST)


def send(to: list[str], subject: str, body: str) -> bool:
    """Send a plain-text email to the given recipients. Returns True if it was
    actually sent over SMTP, False if it was only logged (no SMTP configured
    or no recipients). Never raises -- a missing/misconfigured mailbox
    shouldn't break the caller's business logic (e.g. marking a reminder as
    sent)."""

    recipients = [addr for addr in to if addr]
    if not recipients:
        logger.info("email skipped (no recipients): %s", subject)
        return False

    if not is_configured():
        logger.info("email not sent (SMTP not configured) — to=%s subject=%r\n%s", recipients, subject, body)
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except (smtplib.SMTPException, OSError):
        logger.exception("failed to send email — to=%s subject=%r", recipients, subject)
        return False


def case_recipient_emails(case: Case) -> list[str]:
    """Emails for the people who should hear about a case event: its
    petitioner/beneficiary clients plus the assigned attorney, if any."""

    emails: set[str] = set()
    for participant in case.participants:
        client = participant.client
        if client and client.email and participant.role in (ParticipantRole.PETITIONER, ParticipantRole.BENEFICIARY):
            emails.add(client.email)
    if case.assigned_attorney_id and case.assigned_attorney and case.assigned_attorney.email:
        emails.add(case.assigned_attorney.email)
    return sorted(emails)
