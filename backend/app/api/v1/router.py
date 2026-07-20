from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.endpoints import (
    appointments,
    auth,
    billing,
    cases,
    clients,
    dashboard,
    documents,
    forms,
    gap_analysis,
    notifications,
    public_forms,
    rfes,
    services,
    stats,
    users,
)

api_router = APIRouter()

# Unauthenticated: logging in, and the token-scoped client portal (which has
# its own per-form access_token instead of a login).
api_router.include_router(auth.router)
api_router.include_router(public_forms.router)

# Everything else is internal staff tooling and requires a valid session.
_protected = Depends(get_current_user)
api_router.include_router(clients.router, dependencies=[_protected])
api_router.include_router(cases.router, dependencies=[_protected])
api_router.include_router(forms.router, dependencies=[_protected])
api_router.include_router(users.router, dependencies=[_protected])
api_router.include_router(services.router, dependencies=[_protected])
api_router.include_router(documents.router, dependencies=[_protected])
api_router.include_router(notifications.router, dependencies=[_protected])
api_router.include_router(appointments.router, dependencies=[_protected])
api_router.include_router(billing.router, dependencies=[_protected])
api_router.include_router(stats.router, dependencies=[_protected])
api_router.include_router(rfes.router, dependencies=[_protected])
api_router.include_router(dashboard.router, dependencies=[_protected])
api_router.include_router(gap_analysis.router, dependencies=[_protected])
