import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import (
    ACCESS_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
    CurrentUser,
    DbSession,
    CurrentClient,
)
from app.core.config import settings
from app.core.rate_limit import check_rate_limit, reset_rate_limit
from app.core.security import (
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
    _b64url_encode,
)
from app.models.auth_token import PasswordResetToken, RefreshToken, DeniedToken
from app.models.client import Client
from app.schemas.client import ClientRead
from app.services import email

router = APIRouter(prefix="/client-auth", tags=["client-auth"])

class ClientLoginRequest(BaseModel):
    email: str
    password: str

class AuthenticatedClient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None = None

class ClientTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    client: AuthenticatedClient

class ClientRegisterRequest(BaseModel):
    email: str
    password: str

class ClientRefreshRequest(BaseModel):
    refresh_token: str | None = None

class ClientLogoutRequest(BaseModel):
    refresh_token: str | None = None

class ClientForgotPasswordRequest(BaseModel):
    email: str

class ClientResetPasswordRequest(BaseModel):
    token: str
    password: str


def _cookie_kwargs(max_age_seconds: int) -> dict:
    return {
        "httponly": True,
        "secure": settings.ENVIRONMENT == "production",
        "samesite": "lax",
        "path": "/",
        "max_age": max_age_seconds,
    }


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_TOKEN_COOKIE, access_token, **_cookie_kwargs(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE, refresh_token, **_cookie_kwargs(settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


_DUMMY_PASSWORD_HASH = hash_password(generate_opaque_token())


def create_client_access_token(client_id: uuid.UUID, expires_minutes: int | None = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    payload = {
        "sub": str(client_id),
        "exp": int(time.time()) + minutes * 60,
        "jti": uuid.uuid4().hex,
        "type": "client"
    }

    signing_input = (
        f"{_b64url_encode(json.dumps(header).encode())}." f"{_b64url_encode(json.dumps(payload).encode())}"
    )
    signature = hmac.new(settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _issue_client_tokens(db: DbSession, client: Client) -> ClientTokenResponse:
    access_token = create_client_access_token(client.id)

    raw_refresh_token = generate_opaque_token()
    db.add(
        RefreshToken(
            client_id=client.id,
            token_hash=hash_opaque_token(raw_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()

    return ClientTokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        client=AuthenticatedClient.model_validate(client),
    )


@router.post("/register", response_model=ClientRead)
def register(payload: ClientRegisterRequest, db: DbSession, current_user: CurrentUser):
    # attorney creates a client login: email + password; only staff can do this — use CurrentUser dependency
    client = db.query(Client).filter(func.lower(Client.email) == payload.email.lower()).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client email not found. Client must be created first.")
    
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
    client.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(client)
    return client


@router.post("/login", response_model=ClientTokenResponse)
def login(payload: ClientLoginRequest, db: DbSession, request: Request, response: Response):
    ip = _client_ip(request)
    if not check_rate_limit(
        f"client-login-ip:{ip}", settings.LOGIN_RATE_LIMIT_PER_IP, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    ):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    client = db.query(Client).filter(func.lower(Client.email) == payload.email.lower()).first()

    now = datetime.now(timezone.utc)
    if client and client.locked_until and _as_aware(client.locked_until) > now:
        raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")

    password_valid = verify_password(
        payload.password, client.hashed_password if client and client.hashed_password else _DUMMY_PASSWORD_HASH
    )
    if not client or not client.hashed_password or not password_valid:
        if client:
            client.failed_login_attempts += 1
            if client.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                client.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    client.failed_login_attempts = 0
    client.locked_until = None
    db.commit()
    reset_rate_limit(f"client-login-ip:{ip}")

    tokens = _issue_client_tokens(db, client)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=ClientTokenResponse)
def refresh(payload: ClientRefreshRequest, db: DbSession, request: Request, response: Response):
    raw_refresh_token = payload.refresh_token or request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw_refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    token_hash = hash_opaque_token(raw_refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if not stored or stored.revoked_at is not None or _as_aware(stored.expires_at) < now:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    client = db.get(Client, stored.client_id)
    if not client:
        raise HTTPException(status_code=401, detail="Client not found")

    stored.revoked_at = now
    db.commit()

    tokens = _issue_client_tokens(db, client)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/logout", status_code=204)
def logout(payload: ClientLogoutRequest, db: DbSession, request: Request, response: Response):
    raw_refresh_token = payload.refresh_token or request.cookies.get(REFRESH_TOKEN_COOKIE)
    if raw_refresh_token:
        token_hash = hash_opaque_token(raw_refresh_token)
        stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            db.commit()

    # Revoke access token
    auth_header = request.headers.get("Authorization")
    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
    else:
        access_token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if access_token:
        decoded = decode_access_token(access_token)
        if decoded and "jti" in decoded:
            jti = decoded["jti"]
            exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
            exists = db.query(DeniedToken).filter(DeniedToken.jti == jti).first()
            if not exists:
                db.add(DeniedToken(jti=jti, expires_at=exp))
                db.commit()

    _clear_auth_cookies(response)


@router.post("/forgot-password", status_code=204)
def forgot_password(payload: ClientForgotPasswordRequest, db: DbSession, request: Request):
    ip = _client_ip(request)
    ip_ok = check_rate_limit(
        f"client-forgot-ip:{ip}", settings.FORGOT_PASSWORD_RATE_LIMIT_PER_IP, settings.FORGOT_PASSWORD_RATE_LIMIT_WINDOW_SECONDS
    )
    email_ok = check_rate_limit(
        f"client-forgot-email:{payload.email.lower()}",
        settings.FORGOT_PASSWORD_RATE_LIMIT_PER_IP,
        settings.FORGOT_PASSWORD_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not ip_ok or not email_ok:
        return

    client = db.query(Client).filter(func.lower(Client.email) == payload.email.lower()).first()
    # Always respond 204 whether or not the email exists
    if not client:
        return

    now = datetime.now(timezone.utc)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.client_id == client.id, PasswordResetToken.used_at.is_(None)
    ).update({"used_at": now})

    raw_token = generate_opaque_token()
    db.add(
        PasswordResetToken(
            client_id=client.id,
            token_hash=hash_opaque_token(raw_token),
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )
    db.commit()

    reset_url = f"{settings.CLIENT_PORTAL_BASE_URL}/reset-password/{raw_token}"
    email.send(
        to=[client.email],
        subject="Restablecer tu contraseña de MigratePro",
        body=(
            f"Hola {client.first_name},\n\n"
            f"Para restablecer tu contraseña, abre este enlace (valido por "
            f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos):\n{reset_url}\n\n"
            "Si no pediste esto, ignora este correo."
        ),
    )


@router.post("/reset-password", status_code=204)
def reset_password(payload: ClientResetPasswordRequest, db: DbSession, request: Request):
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    token_hash = hash_opaque_token(payload.token)
    stored = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if not stored or stored.used_at is not None or _as_aware(stored.expires_at) < now:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    client = db.get(Client, stored.client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    client.hashed_password = hash_password(payload.password)
    stored.used_at = now
    
    # Revoke sessions
    db.query(RefreshToken).filter(
        RefreshToken.client_id == client.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": now})

    # Revoke access token
    auth_header = request.headers.get("Authorization")
    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
    else:
        access_token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if access_token:
        decoded = decode_access_token(access_token)
        if decoded and "jti" in decoded:
            jti = decoded["jti"]
            exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
            exists = db.query(DeniedToken).filter(DeniedToken.jti == jti).first()
            if not exists:
                db.add(DeniedToken(jti=jti, expires_at=exp))

    db.commit()


@router.get("/me", response_model=ClientRead)
def me(current_client: CurrentClient):
    return current_client
