from datetime import date

from sqlalchemy.orm import Session

from app.models.case import Case, ParticipantRole
from app.models.client import Client
from app.models.user import User


def _client_dict(client: Client) -> dict:
    return {
        "first_name": client.first_name,
        "last_name": client.last_name,
        "middle_name": "",
        "email": client.email or "",
        "phone": client.phone or "",
        "mobile_phone": client.mobile_phone or "",
        "date_of_birth": client.date_of_birth,
        "country_of_birth": client.country_of_birth or "",
        "nationality": client.nationality or "",
        "a_number": client.a_number or "",
        "passport_number": client.passport_number or "",
        "ssn": client.ssn or "",
        "sex": client.sex or "",
        "marital_status": client.marital_status or "",
        "address_line": client.address_line or "",
        "city": client.city or "",
        "state": client.state or "",
        "zip_code": client.zip_code or "",
        "country": client.country or "",
    }


def _attorney_dict(user: User | None) -> dict:
    if user is None:
        return {}
    parts = user.full_name.split(" ", 1)
    return {
        "first_name": parts[0] if parts else "",
        "last_name": parts[1] if len(parts) > 1 else "",
        "email": user.email or "",
        "phone": user.phone or "",
        "mobile_phone": user.mobile_phone or "",
        "bar_number": user.bar_number or "",
        "firm_name": user.firm_name or "",
        "address_line": user.address_line or "",
        "city": user.city or "",
        "state": user.state or "",
        "zip_code": user.zip_code or "",
    }


def build_case_context(db: Session, case: Case) -> dict:
    """Assemble the data available to fill a form for this case: one entry per
    participant role (petitioner, beneficiary, ...), the assigned attorney, and
    the case's own fields."""

    context: dict = {
        "case": {
            "case_number": case.case_number,
            "case_type": case.case_type.value,
            "status": case.status.value,
        }
    }

    for participant in case.participants:
        role_key = participant.role.value  # "petitioner", "beneficiary", ...
        context[role_key] = _client_dict(participant.client)

    attorney = db.get(User, case.assigned_attorney_id) if case.assigned_attorney_id else None
    context["attorney"] = _attorney_dict(attorney)

    return context


def resolve_source(context: dict, dotted_path: str) -> str:
    """Resolve a 'petitioner.date_of_birth' style path against the context.
    Missing values resolve to '' rather than raising, since not every case
    has every role filled in."""

    node: object = context
    for part in dotted_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return ""
        node = node[part]

    if node is None:
        return ""
    if isinstance(node, date):
        return node.strftime("%m/%d/%Y")
    return str(node)
