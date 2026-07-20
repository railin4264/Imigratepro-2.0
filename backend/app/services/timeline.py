"""Builds the simplified, client-facing case timeline shown in the public
portal (see business model doc: a visual progress tracker meant to reduce
"what's the status of my case" phone calls). This is a representative
generic pipeline, not a per-form-type authoritative workflow -- it's read
entirely off state that already exists on the case (service applied,
generated forms, documents, checklist, status, appointments), nothing new
to maintain. A step is "current" the moment its condition isn't met yet;
everything after it is "pending" even if that step's own condition happens
to be true (e.g. a biometrics appointment logged before the case was
marked filed) -- keeping the display strictly sequential is more legible
for a client than a scattered set of independently-true/false badges."""

from dataclasses import dataclass

from app.models.appointment import AppointmentType
from app.models.case import Case, CaseStatus
from app.models.form import GeneratedFormStatus

_FILED_OR_LATER = {CaseStatus.FILED, CaseStatus.RFE, CaseStatus.APPROVED, CaseStatus.DENIED, CaseStatus.CLOSED}
_DECIDED = {CaseStatus.APPROVED, CaseStatus.DENIED}

STEP_KEYS = [
    "intake",
    "contract",
    "forms",
    "evidence",
    "prepared",
    "filed",
    "biometrics",
    "interview",
    "decision",
]


@dataclass
class TimelineStep:
    key: str
    status: str  # "done" | "current" | "pending"


def build_case_timeline(case: Case) -> list[TimelineStep]:
    appointment_types = {a.appointment_type for a in case.appointments}
    checklist_items = case.checklist_items

    conditions = {
        "intake": True,
        "contract": case.service_id is not None,
        "forms": any(
            gf.status in (GeneratedFormStatus.GENERATED, GeneratedFormStatus.FILED) for gf in case.generated_forms
        ),
        "evidence": len(case.documents) > 0,
        "prepared": bool(checklist_items) and all(item.done for item in checklist_items),
        "filed": case.status in _FILED_OR_LATER,
        "biometrics": AppointmentType.BIOMETRICS in appointment_types,
        "interview": AppointmentType.INTERVIEW in appointment_types,
        "decision": case.status in _DECIDED,
    }

    steps: list[TimelineStep] = []
    current_assigned = False
    for key in STEP_KEYS:
        if current_assigned:
            steps.append(TimelineStep(key=key, status="pending"))
        elif conditions[key]:
            steps.append(TimelineStep(key=key, status="done"))
        else:
            steps.append(TimelineStep(key=key, status="current"))
            current_assigned = True

    return steps
