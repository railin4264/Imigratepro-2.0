import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession, RequireBilling, require_case_access, require_case_access_read
from app.models.billing import Invoice, Payment
from app.models.case import Case
from app.models.notification import NotificationType
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceDetail,
    InvoiceRead,
    InvoiceUpdate,
    PaymentCreate,
    PaymentRead,
)
from app.services import billing
from app.services.audit import log_action
from app.services.notifications import notify
from app.services.reminders import mark_overdue_invoices

router = APIRouter(tags=["billing"])


def _to_read(invoice: Invoice) -> InvoiceRead:
    return InvoiceRead(
        id=invoice.id,
        case_id=invoice.case_id,
        invoice_number=invoice.invoice_number,
        description=invoice.description,
        amount=invoice.amount,
        amount_paid=invoice.amount_paid,
        status=invoice.status,
        due_date=invoice.due_date,
        paid_at=invoice.paid_at,
        created_at=invoice.created_at,
        case_number=invoice.case.case_number if invoice.case else None,
    )


def _next_invoice_number(db: DbSession) -> str:
    count = db.query(Invoice).count()
    return f"INV-{count + 1:05d}"


@router.get("/invoices", response_model=list[InvoiceRead])
def list_invoices(db: DbSession, case_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100):
    query = db.query(Invoice)
    if case_id:
        query = query.filter(Invoice.case_id == case_id)
    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return [_to_read(i) for i in invoices]


@router.get("/cases/{case_id}/invoices", response_model=list[InvoiceRead])
def list_case_invoices(case_id: uuid.UUID, db: DbSession, skip: int = 0, limit: int = 100):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    invoices = (
        db.query(Invoice)
        .filter(Invoice.case_id == case_id)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_to_read(i) for i in invoices]


@router.post("/cases/{case_id}/invoices", response_model=InvoiceRead, status_code=201)
def create_invoice(case_id: uuid.UUID, payload: InvoiceCreate, db: DbSession, requester: RequireBilling):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    invoice = Invoice(case_id=case_id, invoice_number=_next_invoice_number(db), **payload.model_dump())
    db.add(invoice)
    db.flush()
    log_action(
        db,
        requester,
        "invoice.created",
        "invoice",
        invoice.id,
        {"invoice_number": invoice.invoice_number, "amount": invoice.amount, "case_number": case.case_number},
    )
    db.commit()
    db.refresh(invoice)
    return _to_read(invoice)


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    require_case_access_read(case_id=invoice.case_id, current_user=current_user, db=db)
    return InvoiceDetail(**_to_read(invoice).model_dump(), payments=invoice.payments)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceRead)
def update_invoice(invoice_id: uuid.UUID, payload: InvoiceUpdate, db: DbSession, requester: RequireBilling):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    require_case_access(case_id=invoice.case_id, current_user=requester, db=db)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(invoice, field, value)
    # mode="json" here (not the `changes` used to mutate the model above):
    # the audit trail's `details` column is plain JSON, and a raw Enum
    # member or datetime.date isn't serializable as-is.
    log_action(db, requester, "invoice.updated", "invoice", invoice.id, payload.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    db.refresh(invoice)
    return _to_read(invoice)


@router.delete("/invoices/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: uuid.UUID, db: DbSession, requester: RequireBilling):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    require_case_access(case_id=invoice.case_id, current_user=requester, db=db)
    log_action(
        db,
        requester,
        "invoice.deleted",
        "invoice",
        invoice.id,
        {"invoice_number": invoice.invoice_number, "amount": invoice.amount},
    )
    db.delete(invoice)
    db.commit()


@router.post("/invoices/{invoice_id}/payments", response_model=InvoiceDetail, status_code=201)
def add_payment(invoice_id: uuid.UUID, payload: PaymentCreate, db: DbSession, requester: RequireBilling):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    require_case_access(case_id=invoice.case_id, current_user=requester, db=db)

    payment = Payment(
        invoice_id=invoice_id,
        amount=payload.amount,
        method=payload.method,
        paid_at=payload.paid_at or datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.add(payment)
    db.flush()
    billing.recalculate(invoice)
    notify(
        db,
        NotificationType.PAYMENT_RECEIVED,
        f"Payment of {payload.amount:.2f} received for {invoice.invoice_number} ({invoice.case.case_number})",
        case_id=invoice.case_id,
    )
    log_action(
        db,
        requester,
        "invoice.payment_added",
        "payment",
        payment.id,
        {"invoice_number": invoice.invoice_number, "amount": payment.amount, "method": payment.method.value},
    )
    db.commit()
    db.refresh(invoice)
    return InvoiceDetail(**_to_read(invoice).model_dump(), payments=invoice.payments)


@router.delete("/invoices/{invoice_id}/payments/{payment_id}", response_model=InvoiceDetail)
def delete_payment(
    invoice_id: uuid.UUID, payment_id: uuid.UUID, db: DbSession, requester: RequireBilling
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    require_case_access(case_id=invoice.case_id, current_user=requester, db=db)
    payment = db.get(Payment, payment_id)
    if not payment or payment.invoice_id != invoice_id:
        raise HTTPException(status_code=404, detail="Payment not found")

    log_action(
        db,
        requester,
        "invoice.payment_deleted",
        "payment",
        payment.id,
        {"invoice_number": invoice.invoice_number, "amount": payment.amount},
    )
    db.delete(payment)
    db.flush()
    db.refresh(invoice)
    billing.recalculate(invoice)
    db.commit()
    db.refresh(invoice)
    return InvoiceDetail(**_to_read(invoice).model_dump(), payments=invoice.payments)


@router.post("/invoices/mark-overdue")
def mark_overdue(db: DbSession):
    """Flip SENT/PARTIALLY_PAID invoices past their due date to OVERDUE and
    notify. Also runs on its own every SCHEDULER_INTERVAL_MINUTES (see
    app/services/scheduler.py) -- this endpoint is for triggering it on
    demand, not the only way it runs."""
    return mark_overdue_invoices(db)
