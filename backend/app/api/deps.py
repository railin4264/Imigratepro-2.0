import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.models.client import Client

DbSession = Annotated[Session, Depends(get_db)]

# Defined here (not in endpoints/auth.py, which sets/clears them) so both
# that module and this one can import the same names without a circular
# import -- auth.py already depends on this module for CurrentUser/DbSession.
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    # Authorization header first (API clients, the test suite) -- the
    # httpOnly cookie the browser frontend actually uses is the fallback,
    # not the other way round, so nothing that already sends a Bearer token
    # changes behavior.
    token = credentials.credentials if credentials else request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") == "client":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed: UserRole):
    """Dependency factory for endpoints narrower than "any logged-in staff".
    Read access and routine case work (intake, checklist, applying a
    service) intentionally stay open to every role -- this despacho's
    existing design is shared firm-wide visibility, not per-user siloing.
    Reserved for actions that are destructive or move money: deleting a
    case/client/invoice/RFE/document/appointment, and creating or editing
    invoices and payments. A paralegal account being the one that's
    phished or reused elsewhere shouldn't be enough, on its own, to delete
    the firm's billing history."""

    def _check(current_user: CurrentUser) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(r.value for r in allowed)}",
            )
        return current_user

    return _check


RequireAdminOrAttorney = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.ATTORNEY))]

# The audit log is a compliance record of what staff did -- reviewing it is
# an admin-only function, narrower than the destructive/financial actions
# above (which attorneys can also perform, and therefore should be able to
# see logged).
RequireAdmin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


def get_current_client(
    db: DbSession,
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> Client:
    token = credentials.credentials if credentials else request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "client":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    try:
        client_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client not found")

    return client


CurrentClient = Annotated[Client, Depends(get_current_client)]


def get_current_client_optional(
    db: DbSession,
    request: Request,
) -> Client | None:
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "client":
        return None

    try:
        client_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, AttributeError, TypeError):
        return None

    return db.get(Client, client_id)
