from fastapi import APIRouter

from app.api.deps import DbSession, RequireAdmin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogRead

router = APIRouter(prefix="/audit-log", tags=["audit-log"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_log(
    db: DbSession,
    _requester: RequireAdmin,
    entity_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Admin-only: the compliance trail for destructive/financial actions
    (see app.services.audit.log_action). Not exposed to attorney/paralegal
    roles -- this is a record of what staff did, reviewing it is an admin
    function specifically."""

    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    rows = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(min(limit, 500)).all()

    user_names = {u.id: u.full_name for u in db.query(User.id, User.full_name).all()}
    return [
        AuditLogRead(
            id=row.id,
            created_at=row.created_at,
            user_id=row.user_id,
            user_name=user_names.get(row.user_id) if row.user_id else None,
            action=row.action,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            details=row.details,
        )
        for row in rows
    ]
