import uuid
from datetime import date

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.core.security import hash_password
from app.models.case import Case
from app.models.rfe import RFE, RFEStatus
from app.models.service import CaseChecklistItem
from app.models.user import User, UserRole
from app.schemas.auth import SetPasswordRequest
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserWorkload

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, skip: int = 0, limit: int = 100):
    return db.query(User).order_by(User.full_name).offset(skip).limit(limit).all()


@router.get("/workload", response_model=list[UserWorkload])
def list_workload(db: DbSession):
    """Per-staff caseload snapshot for the team overview page -- one query set,
    not N+1 per user, since a firm's whole staff list renders this at once."""

    today = date.today()
    users = db.query(User).order_by(User.full_name).all()
    cases = db.query(Case).filter(Case.assigned_attorney_id.isnot(None)).all()
    open_rfes = db.query(RFE).filter(RFE.status == RFEStatus.OPEN).all()
    overdue_items = (
        db.query(CaseChecklistItem)
        .filter(CaseChecklistItem.done.is_(False), CaseChecklistItem.due_date.isnot(None))
        .filter(CaseChecklistItem.due_date < today)
        .all()
    )

    cases_by_attorney: dict[uuid.UUID, list[Case]] = {}
    for c in cases:
        cases_by_attorney.setdefault(c.assigned_attorney_id, []).append(c)

    case_id_to_attorney = {c.id: c.assigned_attorney_id for c in cases}
    open_rfe_count_by_attorney: dict[uuid.UUID, int] = {}
    for rfe in open_rfes:
        attorney_id = case_id_to_attorney.get(rfe.case_id)
        if attorney_id:
            open_rfe_count_by_attorney[attorney_id] = open_rfe_count_by_attorney.get(attorney_id, 0) + 1

    overdue_count_by_assignee: dict[uuid.UUID, int] = {}
    for item in overdue_items:
        if item.assigned_to_id:
            overdue_count_by_assignee[item.assigned_to_id] = overdue_count_by_assignee.get(item.assigned_to_id, 0) + 1

    result = []
    for user in users:
        user_cases = cases_by_attorney.get(user.id, [])
        by_status: dict[str, int] = {}
        for c in user_cases:
            by_status[c.status.value] = by_status.get(c.status.value, 0) + 1
        result.append(
            UserWorkload(
                user=user,
                assigned_case_count=len(user_cases),
                cases_by_status=by_status,
                open_rfe_count=open_rfe_count_by_attorney.get(user.id, 0),
                overdue_checklist_count=overdue_count_by_assignee.get(user.id, 0),
            )
        )
    return result


@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: DbSession, current_user: CurrentUser):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only an admin can create staff accounts")
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    fields = payload.model_dump(exclude={"password"})
    user = User(**fields)
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: DbSession):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: DbSession, current_user: CurrentUser):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only an admin can edit staff accounts")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    fields = payload.model_dump(exclude_unset=True)
    if fields.get("is_active") is False and user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't deactivate your own account")
    if "role" in fields and fields["role"] != UserRole.ADMIN and user_id == current_user.id:
        if db.query(User).filter(User.role == UserRole.ADMIN, User.id != user_id, User.is_active.is_(True)).count() == 0:
            raise HTTPException(status_code=400, detail="Can't demote the last active admin")

    for field, value in fields.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/password", response_model=UserRead)
def set_password(user_id: uuid.UUID, payload: SetPasswordRequest, db: DbSession, current_user: CurrentUser):
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only an admin can set another user's password")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user
