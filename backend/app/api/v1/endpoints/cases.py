import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    CurrentUser,
    DbSession,
    RequireOwnerOrAdmin,
    require_case_access,
    require_case_access_read,
)
from app.models.case import Case, CaseParticipant
from app.models.client import Client
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate, ParticipantCreate, ParticipantRead
from app.schemas.timeline import CaseTimelineResponse, TimelineStepRead
from app.services.audit import log_action
from app.services.notifications import notify
from app.services.timeline import build_case_timeline

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[CaseRead])
def list_cases(db: DbSession, skip: int = 0, limit: int = 100):
    return db.query(Case).order_by(Case.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=CaseRead, status_code=201)
def create_case(payload: CaseCreate, db: DbSession):
    case = Case(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case: Annotated[Case, Depends(require_case_access_read)]):
    return case


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case: Annotated[Case, Depends(require_case_access)],
    payload: CaseUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    fields = payload.model_dump(exclude_unset=True)
    new_attorney_id = fields.get("assigned_attorney_id")
    attorney_changed = "assigned_attorney_id" in fields and new_attorney_id != case.assigned_attorney_id

    for field, value in fields.items():
        setattr(case, field, value)

    if attorney_changed and new_attorney_id:
        attorney = db.get(User, new_attorney_id)
        if attorney:
            notify(
                db,
                NotificationType.CASE_ASSIGNED,
                f"{case.case_number} assigned to {attorney.full_name}",
                case_id=case.id,
            )

    log_action(db, current_user, "case.updated", "case", case.id, payload.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case: Annotated[Case, Depends(require_case_access)],
    db: DbSession,
    requester: RequireOwnerOrAdmin,
):
    log_action(db, requester, "case.deleted", "case", case.id, {"case_number": case.case_number})
    db.delete(case)
    db.commit()


@router.get("/{case_id}/timeline", response_model=CaseTimelineResponse)
def get_case_timeline(case: Annotated[Case, Depends(require_case_access_read)]):
    steps = build_case_timeline(case)
    return CaseTimelineResponse(
        case_number=case.case_number,
        steps=[TimelineStepRead(key=s.key, status=s.status) for s in steps],
    )


@router.get("/{case_id}/participants", response_model=list[ParticipantRead])
def list_participants(case_id: uuid.UUID, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(CaseParticipant).filter(CaseParticipant.case_id == case_id).all()


@router.post("/{case_id}/participants", response_model=ParticipantRead, status_code=201)
def add_participant(case_id: uuid.UUID, payload: ParticipantCreate, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    participant = CaseParticipant(case_id=case_id, client_id=payload.client_id, role=payload.role)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant
