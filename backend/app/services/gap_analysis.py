"""Rule-based "what's missing" checklist for a case, in the spirit of the
office's manual review pass before a package is considered ready to file.
Every rule here is grounded in fields that actually exist on Case/Client/
Document -- deliberately NOT attempting things like verifying I-864 income
thresholds or chasing "is there a prior marriage that needs a divorce
decree", since neither is captured in the data model and guessing at a
legal sufficiency threshold would be worse than not checking at all. This
mirrors the same judgment call already documented for conditional form
rules (see app/seed_data/conditional_rules.py): real, verifiable checks
only, nothing invented. Always a first pass for the preparer to confirm,
never a filing decision."""

import uuid
from dataclasses import dataclass

from app.models.case import Case, CaseType, ParticipantRole
from app.models.document import DocumentType

_HAS_BOTH_PARTIES = {CaseType.FAMILY_BASED, CaseType.EMPLOYMENT_BASED}


@dataclass
class GapItem:
    severity: str  # "high" | "medium" | "low"
    code: str
    message: str
    client_id: uuid.UUID | None = None


def analyze_case(case: Case) -> list[GapItem]:
    gaps: list[GapItem] = []

    if not case.participants:
        gaps.append(
            GapItem(severity="high", code="no_participants", message="El caso no tiene participantes agregados.")
        )
        return gaps

    roles_present = {p.role for p in case.participants}
    if case.case_type in _HAS_BOTH_PARTIES:
        if ParticipantRole.PETITIONER not in roles_present:
            gaps.append(GapItem(severity="high", code="missing_petitioner", message="Falta agregar al peticionario."))
        if ParticipantRole.BENEFICIARY not in roles_present:
            gaps.append(
                GapItem(severity="high", code="missing_beneficiary", message="Falta agregar al beneficiario.")
            )

    docs_by_client: dict[uuid.UUID, set[DocumentType]] = {}
    for doc in case.documents:
        if doc.client_id:
            docs_by_client.setdefault(doc.client_id, set()).add(doc.document_type)

    for participant in case.participants:
        client = participant.client
        name = f"{client.first_name} {client.last_name}"
        held = docs_by_client.get(client.id, set())

        if DocumentType.PASSPORT not in held and DocumentType.PHOTO_ID not in held:
            gaps.append(
                GapItem(
                    severity="medium",
                    code="missing_photo_id",
                    message=f"Falta el pasaporte o identificación con foto de {name}.",
                    client_id=client.id,
                )
            )

        if participant.role in (ParticipantRole.BENEFICIARY, ParticipantRole.DERIVATIVE):
            if DocumentType.BIRTH_CERTIFICATE not in held:
                gaps.append(
                    GapItem(
                        severity="medium",
                        code="missing_birth_certificate",
                        message=f"Falta el acta de nacimiento de {name}.",
                        client_id=client.id,
                    )
                )

        if client.marital_status == "married" and DocumentType.MARRIAGE_CERTIFICATE not in held:
            gaps.append(
                GapItem(
                    severity="medium",
                    code="missing_marriage_certificate",
                    message=f"{name} figura como casado/a pero no se cargó el acta de matrimonio.",
                    client_id=client.id,
                )
            )

        missing_fields = [
            label
            for value, label in (
                (client.date_of_birth, "fecha de nacimiento"),
                (client.country_of_birth, "país de nacimiento"),
                (client.nationality, "nacionalidad"),
                (client.address_line, "dirección"),
            )
            if not value
        ]
        if missing_fields:
            gaps.append(
                GapItem(
                    severity="low",
                    code="incomplete_profile",
                    message=f"Perfil incompleto de {name}: falta {', '.join(missing_fields)}.",
                    client_id=client.id,
                )
            )

    if case.service and case.service.form_links:
        generated_codes = {gf.template.code for gf in case.generated_forms}
        for link in case.service.form_links:
            if link.form_template.code not in generated_codes:
                gaps.append(
                    GapItem(
                        severity="medium",
                        code="missing_form",
                        message=f"El formulario {link.form_template.code} del servicio aplicado aún no se generó.",
                    )
                )

    return gaps
