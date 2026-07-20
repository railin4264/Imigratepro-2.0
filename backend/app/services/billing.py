from datetime import date, datetime, timezone

from app.models.billing import Invoice, InvoiceStatus


def recalculate(invoice: Invoice) -> None:
    """Derive amount_paid/status/paid_at from the invoice's payments. Called
    after any payment is added or removed so the three never drift out of
    sync with each other."""

    invoice.amount_paid = round(sum(p.amount for p in invoice.payments), 2)

    if invoice.status == InvoiceStatus.CANCELLED:
        return

    if invoice.amount_paid >= invoice.amount and invoice.amount > 0:
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = invoice.payments[-1].paid_at if invoice.payments else datetime.now(timezone.utc)
    elif invoice.amount_paid > 0:
        invoice.status = InvoiceStatus.PARTIALLY_PAID
        invoice.paid_at = None
    elif invoice.due_date and invoice.due_date < date.today() and invoice.status != InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.OVERDUE
        invoice.paid_at = None
    elif invoice.status in (InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE):
        invoice.status = InvoiceStatus.SENT
        invoice.paid_at = None
