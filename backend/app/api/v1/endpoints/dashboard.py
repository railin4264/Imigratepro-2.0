from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.appointment import Appointment
from app.models.case import Case, CaseStatus
from app.models.rfe import RFE, RFEStatus
from app.models.service import CaseChecklistItem
from app.schemas.dashboard import MyDayAppointment, MyDayCase, MyDayChecklistItem, MyDayResponse, MyDayRFE

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _as_aware(dt: datetime) -> datetime:
    """See app/api/v1/endpoints/stats.py::_as_aware -- SQLite hands back naive
    datetimes even for timezone=True columns; treat naive as UTC."""

    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/me", response_model=MyDayResponse)
def my_day(db: DbSession, user: CurrentUser):
    today = date.today()
    day_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Eager-load checklist_items: "cases ready for review" below checks
    # c.checklist_items for every PREPARING case, which would otherwise issue
    # one query per case (N+1) instead of a single batched one.
    my_cases = (
        db.query(Case)
        .filter(Case.assigned_attorney_id == user.id)
        .options(selectinload(Case.checklist_items))
        .all()
    )
    my_case_ids = [c.id for c in my_cases]
    case_number_by_id = {c.id: c.case_number for c in my_cases}

    appointments_today: list[MyDayAppointment] = []
    if my_case_ids:
        todays_appointments = (
            db.query(Appointment)
            .filter(Appointment.case_id.in_(my_case_ids))
            .order_by(Appointment.scheduled_at)
            .all()
        )
        appointments_today = [
            MyDayAppointment(
                id=a.id,
                case_id=a.case_id,
                case_number=case_number_by_id.get(a.case_id, ""),
                appointment_type=a.appointment_type.value,
                scheduled_at=a.scheduled_at,
            )
            for a in todays_appointments
            if day_start <= _as_aware(a.scheduled_at) < day_end
        ]

    checklist_due_items = (
        db.query(CaseChecklistItem)
        .filter(CaseChecklistItem.assigned_to_id == user.id, CaseChecklistItem.done.is_(False))
        .filter(CaseChecklistItem.due_date.isnot(None), CaseChecklistItem.due_date <= today)
        .order_by(CaseChecklistItem.due_date)
        .all()
    )
    checklist_case_ids = {i.case_id for i in checklist_due_items} - set(case_number_by_id)
    if checklist_case_ids:
        for c in db.query(Case).filter(Case.id.in_(checklist_case_ids)).all():
            case_number_by_id[c.id] = c.case_number

    checklist_due = [
        MyDayChecklistItem(
            id=i.id,
            case_id=i.case_id,
            case_number=case_number_by_id.get(i.case_id, ""),
            label=i.label,
            due_date=i.due_date,
            priority=i.priority.value,
            overdue=bool(i.due_date and i.due_date < today),
        )
        for i in checklist_due_items
    ]

    open_rfes: list[MyDayRFE] = []
    if my_case_ids:
        rfes = (
            db.query(RFE)
            .filter(RFE.case_id.in_(my_case_ids), RFE.status == RFEStatus.OPEN)
            .order_by(RFE.response_due_date.is_(None), RFE.response_due_date)
            .all()
        )
        open_rfes = [
            MyDayRFE(
                id=r.id,
                case_id=r.case_id,
                case_number=case_number_by_id.get(r.case_id, ""),
                status=r.status.value,
                response_due_date=r.response_due_date,
            )
            for r in rfes
        ]

    cases_ready_for_review = [
        MyDayCase(id=c.id, case_number=c.case_number, status=c.status.value)
        for c in my_cases
        if c.status == CaseStatus.PREPARING
        and c.checklist_items
        and all(item.done for item in c.checklist_items)
    ]

    return MyDayResponse(
        assigned_case_count=len(my_cases),
        appointments_today=appointments_today,
        checklist_due=checklist_due,
        open_rfes=open_rfes,
        cases_ready_for_review=cases_ready_for_review,
    )
