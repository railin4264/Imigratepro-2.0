"""Appointment-reminder and invoice-overdue sweeps. Shared by the manual
endpoints (`POST /appointments/send-reminders`, `POST /invoices/mark-overdue`)
and the in-process scheduler (`app/services/scheduler.py`) so there's exactly
one implementation of each, not two copies that can drift apart."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.billing import Invoice, InvoiceStatus
from app.models.case import Case
from app.models.notification import NotificationType
from app.models.rfe import RFE, RFEStatus
from app.models.user import UserRole
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
            recipient_user_id=case.assigned_attorney_id,
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
            recipient_role=UserRole.BILLING,
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


def send_case_deadline_reminders(db: Session, days_ahead: int | None = None) -> dict:
    """Notify once per case whose decision_deadline falls within the reminder
    window (e.g. a priority-date-driven filing deadline or a USCIS response
    deadline tracked at the case level). Mirrors send_appointment_reminders'
    sent-flag pattern so a case sitting inside the window across multiple
    sweeps only gets one email."""
    days_ahead = settings.CASE_DEADLINE_REMINDER_DAYS_AHEAD if days_ahead is None else days_ahead
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)
    due = (
        db.query(Case)
        .filter(
            Case.deadline_reminder_sent.is_(False),
            Case.decision_deadline.isnot(None),
            Case.decision_deadline <= cutoff,
            Case.decision_deadline >= now,
        )
        .all()
    )

    sent = 0
    for case in due:
        recipients = email.case_recipient_emails(case)
        email.send(
            to=recipients,
            subject=f"Deadline approaching for {case.case_number}",
            body=(
                f"Case {case.case_number} has a decision deadline of "
                f"{case.decision_deadline.isoformat()}."
            ),
        )
        case.deadline_reminder_sent = True
        notify(
            db,
            NotificationType.CASE_DEADLINE_REMINDER,
            f"Deadline approaching for {case.case_number}: {case.decision_deadline.date().isoformat()}",
            case_id=case.id,
            recipient_user_id=case.assigned_attorney_id,
        )
        sent += 1

    db.commit()
    return {"reminders_sent": sent, "checked": len(due)}


def send_rfe_deadline_reminders(db: Session, days_ahead: int | None = None) -> dict:
    """Notify once per open RFE whose response_due_date falls within the
    reminder window. Missing an RFE deadline can mean a denial, so this is
    scoped to RFEStatus.OPEN only -- once a response was submitted (or the
    RFE closed), there's nothing left to remind anyone about."""
    days_ahead = settings.RFE_DEADLINE_REMINDER_DAYS_AHEAD if days_ahead is None else days_ahead
    today = datetime.now(timezone.utc).date()
    cutoff = today + timedelta(days=days_ahead)
    due = (
        db.query(RFE)
        .filter(
            RFE.status == RFEStatus.OPEN,
            RFE.deadline_reminder_sent.is_(False),
            RFE.response_due_date.isnot(None),
            RFE.response_due_date <= cutoff,
            RFE.response_due_date >= today,
        )
        .all()
    )

    sent = 0
    for rfe in due:
        case = rfe.case
        email.send(
            to=email.case_recipient_emails(case),
            subject=f"RFE response due soon for {case.case_number}",
            body=(
                f"Case {case.case_number} has an RFE response due on "
                f"{rfe.response_due_date.isoformat()}."
            ),
        )
        rfe.deadline_reminder_sent = True
        notify(
            db,
            NotificationType.RFE_DEADLINE_REMINDER,
            f"RFE response due soon for {case.case_number}: {rfe.response_due_date.isoformat()}",
            case_id=case.id,
            recipient_user_id=case.assigned_attorney_id,
        )
        sent += 1

    db.commit()
    return {"reminders_sent": sent, "checked": len(due)}
