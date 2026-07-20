from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import func

from app.api.deps import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, CurrentUser, DbSession
from app.core.config import settings
from app.core.rate_limit import check_rate_limit, reset_rate_limit
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models.auth_token import PasswordResetToken, RefreshToken
from app.models.user import User
from app.schemas.auth import (
    AuthenticatedUser,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services import email

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie-based auth for the browser frontend, alongside (not instead of) the
# existing Bearer-token flow in the JSON body -- see get_current_user (in
# app.api.deps, which also defines ACCESS_TOKEN_COOKIE/REFRESH_TOKEN_COOKIE),
# which checks the Authorization header first and falls back to these
# cookies. Kept dual-mode on purpose: any non-browser API client (scripts,
# the test suite) keeps working against the body tokens unchanged, while the
# actual browser stops needing to store anything a same-origin XSS payload
# could read (localStorage is JS-visible; an httpOnly cookie isn't).


def _cookie_kwargs(max_age_seconds: int) -> dict:
    return {
        "httponly": True,
        # Secure requires HTTPS -- forcing it on unconditionally would make
        # every cookie silently fail to be sent on a plain-HTTP local dev
        # server. Same ENVIRONMENT gate as the SECRET_KEY startup check.
        "secure": settings.ENVIRONMENT == "production",
        # Lax (not None): frontend and backend are same-site in every
        # deployment this app documents (same registrable domain, different
        # port/subdomain), so Lax covers normal same-site fetches while
        # still blocking the cross-site POST/PUT/DELETE requests CSRF relies
        # on -- a real cross-origin attacker page's fetch() wouldn't carry
        # this cookie at all. A deployment that puts the API on a genuinely
        # different registrable domain would need SameSite=None; Secure=True
        # instead, which is a deployment-specific call, not a default to
        # guess here.
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

# A precomputed PBKDF2 hash with no corresponding real password, spent on
# every login attempt for an email that doesn't exist. Without this,
# `verify_password` (deliberately slow, ~260k PBKDF2 iterations) only runs
# when `user` is truthy, so a nonexistent email returns measurably faster
# than a wrong password for a real one -- an attacker timing responses could
# use that to enumerate registered emails even though the error message
# itself is identical either way.
_DUMMY_PASSWORD_HASH = hash_password(generate_opaque_token())


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _as_aware(dt: datetime) -> datetime:
    """SQLite hands back naive datetimes for DateTime(timezone=True) columns
    (Postgres doesn't) -- normalize before comparing against aware "now"."""

    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _issue_tokens(db: DbSession, user: User) -> TokenResponse:
    access_token = create_access_token(user.id)

    raw_refresh_token = generate_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user=AuthenticatedUser.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession, request: Request, response: Response):
    ip = _client_ip(request)
    if not check_rate_limit(
        f"login-ip:{ip}", settings.LOGIN_RATE_LIMIT_PER_IP, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    ):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    # Case-insensitive: emails aren't meaningfully distinct by case, and a
    # browser/OS auto-capitalizing the first letter shouldn't turn into an
    # "account not found" masquerading as "wrong password" (both give the
    # same generic message, so this was silently unfixable from the outside).
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()

    now = datetime.now(timezone.utc)
    if user and user.locked_until and _as_aware(user.locked_until) > now:
        raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")

    password_valid = verify_password(
        payload.password, user.hashed_password if user and user.hashed_password else _DUMMY_PASSWORD_HASH
    )
    if not user or not user.hashed_password or not password_valid:
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is inactive")

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    reset_rate_limit(f"login-ip:{ip}")

    tokens = _issue_tokens(db, user)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DbSession, request: Request, response: Response):
    raw_refresh_token = payload.refresh_token or request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw_refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    token_hash = hash_opaque_token(raw_refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if not stored or stored.revoked_at is not None or _as_aware(stored.expires_at) < now:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.get(User, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Rotate: this refresh token is single-use, so a replayed/stolen copy
    # stops working the moment the legitimate client refreshes again.
    stored.revoked_at = now
    db.commit()

    tokens = _issue_tokens(db, user)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/logout", status_code=204)
def logout(payload: LogoutRequest, db: DbSession, request: Request, response: Response):
    raw_refresh_token = payload.refresh_token or request.cookies.get(REFRESH_TOKEN_COOKIE)
    if raw_refresh_token:
        token_hash = hash_opaque_token(raw_refresh_token)
        stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            db.commit()
    _clear_auth_cookies(response)


@router.get("/me", response_model=AuthenticatedUser)
def me(current_user: CurrentUser):
    return current_user


@router.post("/forgot-password", status_code=204)
def forgot_password(payload: ForgotPasswordRequest, db: DbSession, request: Request):
    ip = _client_ip(request)
    # Rate-limited by IP *and* by the target email, separately: the IP limit
    # stops one source spamming many inboxes, the email limit stops many
    # sources (or a retried browser tab) spamming one inbox.
    ip_ok = check_rate_limit(
        f"forgot-ip:{ip}", settings.FORGOT_PASSWORD_RATE_LIMIT_PER_IP, settings.FORGOT_PASSWORD_RATE_LIMIT_WINDOW_SECONDS
    )
    email_ok = check_rate_limit(
        f"forgot-email:{payload.email.lower()}",
        settings.FORGOT_PASSWORD_RATE_LIMIT_PER_IP,
        settings.FORGOT_PASSWORD_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not ip_ok or not email_ok:
        # Still 204: rate-limiting a nonexistent email with a different
        # status would itself leak whether the email exists.
        return

    # Case-insensitive: emails aren't meaningfully distinct by case, and a
    # browser/OS auto-capitalizing the first letter shouldn't turn into an
    # "account not found" masquerading as "wrong password" (both give the
    # same generic message, so this was silently unfixable from the outside).
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    # Always respond 204 whether or not the email exists -- a different
    # response would let a caller enumerate which emails have accounts.
    if not user or not user.is_active:
        return

    now = datetime.now(timezone.utc)
    # Invalidate any reset links already sent so only the newest one works --
    # otherwise an old email sitting in an inbox (or a leaked one) stays a
    # valid way in even after the user asked for a fresh link.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
    ).update({"used_at": now})

    raw_token = generate_opaque_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_token),
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )
    db.commit()

    reset_url = f"{settings.CLIENT_PORTAL_BASE_URL}/reset-password/{raw_token}"
    email.send(
        to=[user.email],
        subject="Restablecer tu contraseña de MigratePro",
        body=(
            f"Hola {user.full_name},\n\n"
            f"Para restablecer tu contraseña, abre este enlace (valido por "
            f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos):\n{reset_url}\n\n"
            "Si no pediste esto, ignora este correo."
        ),
    )


@router.post("/reset-password", status_code=204)
def reset_password(payload: ResetPasswordRequest, db: DbSession):
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    token_hash = hash_opaque_token(payload.token)
    stored = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if not stored or stored.used_at is not None or _as_aware(stored.expires_at) < now:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user = db.get(User, stored.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user.hashed_password = hash_password(payload.password)
    stored.used_at = now
    # A password reset is a strong signal to also kill any existing sessions.
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": now})
    db.commit()
