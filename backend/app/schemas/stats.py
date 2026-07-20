from datetime import date

from pydantic import BaseModel


class CountByKey(BaseModel):
    key: str
    count: int


class StatsOverview(BaseModel):
    total_clients: int
    total_cases: int
    open_cases: int
    cases_by_status: list[CountByKey]
    cases_by_type: list[CountByKey]
    total_documents: int
    upcoming_appointments_7d: int
    overdue_appointments: int
    total_invoiced: float
    total_collected: float
    total_outstanding: float
    overdue_invoice_count: int
    cases_created_last_30d: list[CountByKey]


class RevenuePoint(BaseModel):
    month: str
    invoiced: float
    collected: float
