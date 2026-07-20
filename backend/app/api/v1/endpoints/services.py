import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.api.v1.endpoints.forms import _initial_data, _render_pdf
from app.models.case import Case
from app.models.form import FormTemplate, GeneratedForm, GeneratedFormStatus
from app.models.notification import NotificationType
from app.models.service import (
    CaseChecklistItem,
    Service,
    ServiceChecklistItem,
    ServiceFormTemplate,
    WorkflowStage,
)
from app.schemas.service import (
    ApplyServiceRequest,
    CaseServiceView,
    ChecklistItemRead,
    ChecklistItemUpdate,
    ServiceCreate,
    ServiceRead,
)
from app.services.notifications import notify

router = APIRouter(tags=["services"])


def _service_read(db: Session, service: Service) -> ServiceRead:
    form_codes = []
    for link in service.form_links:
        template = db.get(FormTemplate, link.form_template_id)
        if template:
            form_codes.append(template.code)

    return ServiceRead(
        id=service.id,
        name=service.name,
        description=service.description,
        price=service.price,
        estimated_days=service.estimated_days,
        created_at=service.created_at,
        form_codes=form_codes,
        checklist_items=[item.label for item in service.checklist_items],
        stages=[stage.name for stage in service.stages],
    )


def _case_service_view(db: Session, case: Case) -> CaseServiceView:
    service = db.get(Service, case.service_id) if case.service_id else None
    current_stage = db.get(WorkflowStage, case.workflow_stage_id) if case.workflow_stage_id else None

    current_index = None
    if current_stage and service:
        for idx, stage in enumerate(service.stages):
            if stage.id == current_stage.id:
                current_index = idx
                break

    checklist = (
        db.query(CaseChecklistItem)
        .filter_by(case_id=case.id)
        .order_by(CaseChecklistItem.order)
        .all()
    )

    return CaseServiceView(
        service=_service_read(db, service) if service else None,
        stages=[stage.name for stage in service.stages] if service else [],
        current_stage=current_stage.name if current_stage else None,
        current_stage_index=current_index,
        checklist=[ChecklistItemRead.model_validate(item) for item in checklist],
    )


@router.get("/services", response_model=list[ServiceRead])
def list_services(db: DbSession, skip: int = 0, limit: int = 100):
    services = db.query(Service).order_by(Service.name).offset(skip).limit(limit).all()
    return [_service_read(db, s) for s in services]


@router.post("/services", response_model=ServiceRead, status_code=201)
def create_service(payload: ServiceCreate, db: DbSession):
    service = Service(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        estimated_days=payload.estimated_days,
    )
    db.add(service)
    db.flush()

    for index, stage_name in enumerate(payload.stages):
        db.add(WorkflowStage(service_id=service.id, name=stage_name, order=index))
    for index, label in enumerate(payload.checklist_items):
        db.add(ServiceChecklistItem(service_id=service.id, label=label, order=index))
    for code in payload.form_template_codes:
        template = db.query(FormTemplate).filter_by(code=code).one_or_none()
        if template:
            db.add(ServiceFormTemplate(service_id=service.id, form_template_id=template.id))

    db.commit()
    db.refresh(service)
    return _service_read(db, service)


@router.get("/cases/{case_id}/service", response_model=CaseServiceView)
def get_case_service(case_id: uuid.UUID, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_service_view(db, case)


@router.post("/cases/{case_id}/apply-service", response_model=CaseServiceView, status_code=201)
def apply_service(case_id: uuid.UUID, payload: ApplyServiceRequest, db: DbSession):
    """Assign a service package to a case: materializes its checklist onto the
    case, sets the case to the service's first workflow stage, and
    auto-generates a draft of every form the service bundles."""

    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    service = db.get(Service, payload.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    case.service_id = service.id
    case.workflow_stage_id = service.stages[0].id if service.stages else None

    for item in service.checklist_items:
        db.add(CaseChecklistItem(case_id=case.id, label=item.label, order=item.order))

    for link in service.form_links:
        template = db.get(FormTemplate, link.form_template_id)
        if not template or not template.pdf_template_path:
            continue
        generated = GeneratedForm(
            case_id=case.id,
            form_template_id=template.id,
            status=GeneratedFormStatus.DRAFT,
            data=_initial_data(db, template, case),
        )
        db.add(generated)
        db.flush()
        _render_pdf(template, generated)

    db.commit()
    db.refresh(case)
    return _case_service_view(db, case)


@router.patch("/cases/{case_id}/checklist/{item_id}", response_model=ChecklistItemRead)
def update_checklist_item(
    case_id: uuid.UUID, item_id: uuid.UUID, payload: ChecklistItemUpdate, db: DbSession
):
    item = db.get(CaseChecklistItem, item_id)
    if not item or item.case_id != case_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    fields = payload.model_dump(exclude_unset=True)
    if "done" in fields:
        item.done = fields["done"]
        item.done_at = datetime.now(timezone.utc) if fields["done"] else None
    if "assigned_to_id" in fields:
        item.assigned_to_id = fields["assigned_to_id"]
    if "due_date" in fields:
        item.due_date = fields["due_date"]
    if "priority" in fields:
        item.priority = fields["priority"]

    db.commit()
    db.refresh(item)
    return item


@router.post("/cases/{case_id}/advance-stage", response_model=CaseServiceView)
def advance_stage(case_id: uuid.UUID, db: DbSession):
    case = db.get(Case, case_id)
    if not case or not case.service_id:
        raise HTTPException(status_code=404, detail="Case has no service applied")

    service = db.get(Service, case.service_id)
    stages = service.stages if service else []

    current_index = None
    for idx, stage in enumerate(stages):
        if stage.id == case.workflow_stage_id:
            current_index = idx
            break

    if current_index is None:
        next_stage = stages[0] if stages else None
    elif current_index + 1 < len(stages):
        next_stage = stages[current_index + 1]
    else:
        next_stage = stages[current_index]

    case.workflow_stage_id = next_stage.id if next_stage else None
    if next_stage:
        notify(
            db,
            NotificationType.STAGE_ADVANCED,
            f'{case.case_number} moved to "{next_stage.name}"',
            case_id=case.id,
        )
    db.commit()
    db.refresh(case)
    return _case_service_view(db, case)
