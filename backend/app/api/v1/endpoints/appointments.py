import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession, RequireAdminOrAttorney, require_case_access
from app.models.appointment import Appointment
from app.models.case import Case
from app.models.notification import NotificationType
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.services.audit import log_action
from app.services.notifications import notify
from app.services.reminders import send_appointment_reminders

router = APIRouter(tags=["appointments"])


def _to_read(appointment: Appointment) -> AppointmentRead:
    return AppointmentRead(
        id=appointment.id,
        case_id=appointment.case_id,
        appointment_type=appointment.appointment_type,
        scheduled_at=appointment.scheduled_at,
        location=appointment.location,
        notes=appointment.notes,
        reminder_sent=appointment.reminder_sent,
        created_at=appointment.created_at,
        case_number=appointment.case.case_number if appointment.case else None,
    )


@router.get("/appointments", response_model=list[AppointmentRead])
def list_appointments(
    db: DbSession,
    case_id: uuid.UUID | None = None,
    upcoming_only: bool = False,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(Appointment)
    if case_id:
        query = query.filter(Appointment.case_id == case_id)
    if upcoming_only:
        query = query.filter(Appointment.scheduled_at >= datetime.now(timezone.utc))
    appointments = query.order_by(Appointment.scheduled_at.asc()).offset(skip).limit(limit).all()
    return [_to_read(a) for a in appointments]


@router.get("/cases/{case_id}/appointments", response_model=list[AppointmentRead])
def list_case_appointments(case_id: uuid.UUID, db: DbSession, skip: int = 0, limit: int = 100):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    appointments = (
        db.query(Appointment)
        .filter(Appointment.case_id == case_id)
        .order_by(Appointment.scheduled_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_to_read(a) for a in appointments]


@router.post("/cases/{case_id}/appointments", response_model=AppointmentRead, status_code=201)
def create_appointment(case_id: uuid.UUID, payload: AppointmentCreate, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    appointment = Appointment(case_id=case_id, **payload.model_dump())
    db.add(appointment)
    notify(
        db,
        NotificationType.APPOINTMENT_SCHEDULED,
        f"{appointment.appointment_type.value.replace('_', ' ').title()} scheduled for {case.case_number}",
        case_id=case.id,
        recipient_user_id=case.assigned_attorney_id,
    )
    db.commit()
    db.refresh(appointment)
    return _to_read(appointment)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentRead)
def update_appointment(appointment_id: uuid.UUID, payload: AppointmentUpdate, db: DbSession, current_user: CurrentUser):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    require_case_access(case_id=appointment.case_id, current_user=current_user, db=db)

    fields = payload.model_dump(exclude_unset=True)
    if "scheduled_at" in fields:
        # A rescheduled appointment should get a fresh reminder later on.
        appointment.reminder_sent = False
    for field, value in fields.items():
        setattr(appointment, field, value)

    log_action(db, current_user, "appointment.updated", "appointment", appointment.id, payload.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    db.refresh(appointment)
    return _to_read(appointment)


@router.delete("/appointments/{appointment_id}", status_code=204)
def delete_appointment(appointment_id: uuid.UUID, db: DbSession, requester: RequireAdminOrAttorney):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    require_case_access(case_id=appointment.case_id, current_user=requester, db=db)
    log_action(
        db,
        requester,
        "appointment.deleted",
        "appointment",
        appointment.id,
        {"appointment_type": appointment.appointment_type.value, "case_number": appointment.case.case_number},
    )
    db.delete(appointment)
    db.commit()


@router.post("/appointments/send-reminders")
def send_reminders(db: DbSession, hours_ahead: int = 48):
    """Send (or log) reminder emails for appointments coming up within the
    given window that haven't been reminded about yet. Also runs on its own
    every SCHEDULER_INTERVAL_MINUTES (see app/services/scheduler.py) -- this
    endpoint is for triggering it on demand (e.g. right after seeding demo
    data) rather than the only way it runs."""
    return send_appointment_reminders(db, hours_ahead)
