from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.appointment import Appointment
from app.models.billing import Invoice, InvoiceStatus, Payment
from app.models.case import Case, CaseStatus
from app.models.client import Client
from app.models.document import Document
from app.schemas.stats import CountByKey, RevenuePoint, StatsOverview

router = APIRouter(prefix="/stats", tags=["stats"])

_OPEN_STATUSES = {CaseStatus.INTAKE, CaseStatus.PREPARING, CaseStatus.FILED, CaseStatus.RFE}


def _as_aware(dt: datetime) -> datetime:
    """SQLite ignores the timezone=True on our DateTime columns and hands
    back naive datetimes (Postgres doesn't), so a naive value here is always
    UTC -- just unlabeled. Normalize before comparing against an aware "now"
    to avoid `TypeError: can't compare offset-naive and offset-aware
    datetimes` on sqlite (the default local dev database)."""

    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/overview", response_model=StatsOverview)
def overview(db: DbSession):
    now = datetime.now(timezone.utc)
    today = now.date()

    cases = db.query(Case).all()
    invoices = db.query(Invoice).all()
    appointments = db.query(Appointment).all()

    cases_by_status = Counter(c.status.value for c in cases)
    cases_by_type = Counter(c.case_type.value for c in cases)

    created_by_day: Counter[str] = Counter()
    cutoff = today - timedelta(days=30)
    for c in cases:
        created_date = c.created_at.date()
        if created_date >= cutoff:
            created_by_day[created_date.isoformat()] += 1

    upcoming_7d = sum(
        1 for a in appointments if now <= _as_aware(a.scheduled_at) <= now + timedelta(days=7)
    )
    overdue_appointments = sum(
        1 for a in appointments if not a.reminder_sent and _as_aware(a.scheduled_at) < now
    )

    total_invoiced = round(sum(i.amount for i in invoices), 2)
    total_collected = round(sum(i.amount_paid for i in invoices), 2)
    overdue_count = sum(1 for i in invoices if i.status == InvoiceStatus.OVERDUE)

    return StatsOverview(
        total_clients=db.query(Client).count(),
        total_cases=len(cases),
        open_cases=sum(1 for c in cases if c.status in _OPEN_STATUSES),
        cases_by_status=[CountByKey(key=k, count=v) for k, v in sorted(cases_by_status.items())],
        cases_by_type=[CountByKey(key=k, count=v) for k, v in sorted(cases_by_type.items())],
        total_documents=db.query(Document).count(),
        upcoming_appointments_7d=upcoming_7d,
        overdue_appointments=overdue_appointments,
        total_invoiced=total_invoiced,
        total_collected=total_collected,
        total_outstanding=round(total_invoiced - total_collected, 2),
        overdue_invoice_count=overdue_count,
        cases_created_last_30d=[CountByKey(key=k, count=v) for k, v in sorted(created_by_day.items())],
    )


@router.get("/revenue", response_model=list[RevenuePoint])
def revenue_by_month(db: DbSession, months: int = 6):
    invoices = db.query(Invoice).all()
    payments = db.query(Payment).all()

    today = date.today()
    buckets: list[str] = []
    cursor = today.replace(day=1)
    for _ in range(months):
        buckets.append(cursor.strftime("%Y-%m"))
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    buckets.reverse()

    invoiced_by_month: Counter[str] = Counter()
    for inv in invoices:
        month = inv.created_at.strftime("%Y-%m")
        invoiced_by_month[month] += inv.amount

    collected_by_month: Counter[str] = Counter()
    for pmt in payments:
        month = pmt.paid_at.strftime("%Y-%m")
        collected_by_month[month] += pmt.amount

    return [
        RevenuePoint(
            month=month,
            invoiced=round(invoiced_by_month.get(month, 0), 2),
            collected=round(collected_by_month.get(month, 0), 2),
        )
        for month in buckets
    ]
