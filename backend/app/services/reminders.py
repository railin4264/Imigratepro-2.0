"""Appointment-reminder and invoice-overdue sweeps. Shared by the manual
endpoints (`POST /appointments/send-reminders`, `POST /invoices/mark-overdue`)
and the in-process scheduler (`app/services/scheduler.py`) so there's exactly
one implementation of each, not two copies that can drift apart."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.billing import Invoice, InvoiceStatus
from app.models.notification import NotificationType
from app.services import email
from app.services.notifications import notify


def send_appointment_reminders(db: Session, hours_ahead: int | None = None) -> dict:
    hours_ahead = settings.APPOINTMENT_REMINDER_HOURS_AHEAD if hours_ahead is None else hours_ahead
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours_ahead)
    due = (
        db.query(Appointment)
        .filter(
            Appointment.reminder_sent.is_(False),
            Appointment.scheduled_at <= cutoff,
            Appointment.scheduled_at >= now,
        )
        .all()
    )

    sent = 0
    for appointment in due:
        case = appointment.case
        recipients = email.case_recipient_emails(case)
        email.send(
            to=recipients,
            subject=f"Reminder: {appointment.appointment_type.value.replace('_', ' ').title()} for {case.case_number}",
            body=(
                f"This is a reminder that case {case.case_number} has a "
                f"{appointment.appointment_type.value.replace('_', ' ')} scheduled for "
                f"{appointment.scheduled_at.isoformat()}."
                + (f"\nLocation: {appointment.location}" if appointment.location else "")
            ),
        )
        appointment.reminder_sent = True
        notify(
            db,
            NotificationType.APPOINTMENT_REMINDER,
            f"Reminder sent for {case.case_number}: {appointment.appointment_type.value.replace('_', ' ')}",
            case_id=case.id,
        )
        sent += 1

    db.commit()
    return {"reminders_sent": sent, "checked": len(due)}


def mark_overdue_invoices(db: Session) -> dict:
    today = datetime.now(timezone.utc).date()
    candidates = (
        db.query(Invoice).filter(Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID])).all()
    )

    flagged = 0
    for invoice in candidates:
        if not invoice.due_date or invoice.due_date >= today:
            continue
        invoice.status = InvoiceStatus.OVERDUE
        notify(
            db,
            NotificationType.INVOICE_OVERDUE,
            f"{invoice.invoice_number} ({invoice.case.case_number}) is overdue",
            case_id=invoice.case_id,
        )
        email.send(
            to=email.case_recipient_emails(invoice.case),
            subject=f"Invoice {invoice.invoice_number} is overdue",
            body=(
                f"Invoice {invoice.invoice_number} for case {invoice.case.case_number} "
                f"(amount {invoice.amount:.2f}, balance {invoice.amount - invoice.amount_paid:.2f}) "
                f"was due on {invoice.due_date.isoformat()} and is now overdue."
            ),
        )
        flagged += 1

    db.commit()
    return {"marked_overdue": flagged, "checked": len(candidates)}
