import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.models.case import Case, CaseStatus
from app.models.notification import NotificationType
from app.models.rfe import RFE, RFEEvidenceItem, RFEEvidenceStatus, RFEStatus
from app.schemas.rfe import (
    EvidenceItemCreate,
    EvidenceItemRead,
    EvidenceItemUpdate,
    RFECreate,
    RFEDetail,
    RFERead,
    RFESuggestRequest,
    RFESuggestResponse,
    RFEUpdate,
)
from app.services import rfe_ai
from app.services.notifications import notify

router = APIRouter(tags=["rfes"])


def _to_read(rfe: RFE) -> RFERead:
    return RFERead(
        id=rfe.id,
        case_id=rfe.case_id,
        case_number=rfe.case.case_number if rfe.case else None,
        status=rfe.status,
        received_date=rfe.received_date,
        response_due_date=rfe.response_due_date,
        notes=rfe.notes,
        created_at=rfe.created_at,
        evidence_count=len(rfe.evidence_items),
        evidence_gathered_count=sum(
            1 for i in rfe.evidence_items if i.status != RFEEvidenceStatus.PENDING
        ),
    )


def _to_detail(rfe: RFE) -> RFEDetail:
    return RFEDetail(**_to_read(rfe).model_dump(), raw_text=rfe.raw_text, evidence_items=rfe.evidence_items)


@router.get("/rfes", response_model=list[RFERead])
def list_rfes(db: DbSession, status: RFEStatus | None = None, skip: int = 0, limit: int = 100):
    query = db.query(RFE)
    if status:
        query = query.filter(RFE.status == status)
    rfes = query.order_by(RFE.received_date.desc()).offset(skip).limit(limit).all()
    return [_to_read(r) for r in rfes]


@router.get("/cases/{case_id}/rfes", response_model=list[RFERead])
def list_case_rfes(case_id: uuid.UUID, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    rfes = db.query(RFE).filter(RFE.case_id == case_id).order_by(RFE.received_date.desc()).all()
    return [_to_read(r) for r in rfes]


@router.post("/cases/{case_id}/rfes", response_model=RFERead, status_code=201)
def create_rfe(case_id: uuid.UUID, payload: RFECreate, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    rfe = RFE(case_id=case_id, **payload.model_dump())
    db.add(rfe)
    # An RFE landing is significant enough to flip the case status too, same
    # spirit as the existing status field -- but only nudge it forward, never
    # override a status the preparer may have already moved past (e.g. denied).
    if case.status in (CaseStatus.INTAKE, CaseStatus.PREPARING, CaseStatus.FILED):
        case.status = CaseStatus.RFE
    notify(db, NotificationType.RFE_RECEIVED, f"RFE recorded for {case.case_number}", case_id=case.id)
    db.commit()
    db.refresh(rfe)
    return _to_read(rfe)


@router.get("/rfes/ai-status")
def ai_status():
    return {"configured": rfe_ai.is_configured()}


@router.get("/rfes/{rfe_id}", response_model=RFEDetail)
def get_rfe(rfe_id: uuid.UUID, db: DbSession):
    rfe = db.get(RFE, rfe_id)
    if not rfe:
        raise HTTPException(status_code=404, detail="RFE not found")
    return _to_detail(rfe)


@router.patch("/rfes/{rfe_id}", response_model=RFEDetail)
def update_rfe(rfe_id: uuid.UUID, payload: RFEUpdate, db: DbSession):
    rfe = db.get(RFE, rfe_id)
    if not rfe:
        raise HTTPException(status_code=404, detail="RFE not found")

    fields = payload.model_dump(exclude_unset=True)
    was_open = rfe.status == RFEStatus.OPEN
    for field, value in fields.items():
        setattr(rfe, field, value)

    # Mirror image of create_rfe's forward nudge: once the last open RFE on
    # a case is resolved, the case shouldn't be stuck showing "RFE" on the
    # board forever -- move it back to "filed" (only if nothing else moved
    # it on in the meantime, and only if no other RFE on this case is still
    # open, since a case can accumulate more than one over time).
    if was_open and rfe.status != RFEStatus.OPEN and rfe.case.status == CaseStatus.RFE:
        other_open = (
            db.query(RFE)
            .filter(RFE.case_id == rfe.case_id, RFE.id != rfe.id, RFE.status == RFEStatus.OPEN)
            .first()
        )
        if not other_open:
            rfe.case.status = CaseStatus.FILED

    db.commit()
    db.refresh(rfe)
    return _to_detail(rfe)


@router.delete("/rfes/{rfe_id}", status_code=204)
def delete_rfe(rfe_id: uuid.UUID, db: DbSession):
    rfe = db.get(RFE, rfe_id)
    if not rfe:
        raise HTTPException(status_code=404, detail="RFE not found")
    db.delete(rfe)
    db.commit()


@router.post("/rfes/{rfe_id}/evidence", response_model=EvidenceItemRead, status_code=201)
def add_evidence_item(rfe_id: uuid.UUID, payload: EvidenceItemCreate, db: DbSession):
    rfe = db.get(RFE, rfe_id)
    if not rfe:
        raise HTTPException(status_code=404, detail="RFE not found")

    order = len(rfe.evidence_items)
    item = RFEEvidenceItem(rfe_id=rfe_id, description=payload.description, order=order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/rfes/{rfe_id}/evidence/{item_id}", response_model=EvidenceItemRead)
def update_evidence_item(rfe_id: uuid.UUID, item_id: uuid.UUID, payload: EvidenceItemUpdate, db: DbSession):
    item = db.get(RFEEvidenceItem, item_id)
    if not item or item.rfe_id != rfe_id:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/rfes/{rfe_id}/evidence/{item_id}", status_code=204)
def delete_evidence_item(rfe_id: uuid.UUID, item_id: uuid.UUID, db: DbSession):
    item = db.get(RFEEvidenceItem, item_id)
    if not item or item.rfe_id != rfe_id:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    db.delete(item)
    db.commit()


@router.post("/rfes/{rfe_id}/suggest", response_model=RFESuggestResponse)
def suggest_evidence(rfe_id: uuid.UUID, payload: RFESuggestRequest, db: DbSession):
    rfe = db.get(RFE, rfe_id)
    if not rfe:
        raise HTTPException(status_code=404, detail="RFE not found")
    if not rfe_ai.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AI evidence suggestions are not configured: set ANTHROPIC_API_KEY in backend/.env",
        )

    text = payload.raw_text or rfe.raw_text
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No RFE text to analyze -- paste the notice text first")

    try:
        result = rfe_ai.suggest_evidence(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Suggestion generation failed: {exc}") from exc

    return RFESuggestResponse(**result)
