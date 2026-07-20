"""Password hashing, JWT (HS256) issuing/verification, and opaque token
hashing for refresh/password-reset tokens -- all hand-rolled with only the
standard library so auth doesn't need a new dependency.

Sessions combine a short-lived JWT access token (self-contained, cheap to
verify, not revocable before it expires) with a long-lived opaque refresh
token (stored server-side as a hash, so it *can* be revoked on logout and is
rotated on every use). Still no key rotation or multi-secret support -- fine
for a single-secret MVP, not a drop-in for a multi-tenant production identity
system."""

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid

from app.core.config import settings

_PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, digest_hex = hashed.split("$", 1)
    except ValueError:
        return False
    expected = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS)
    return hmac.compare_digest(expected.hex(), digest_hex)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(user_id: uuid.UUID, expires_minutes: int | None = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    # `jti` is otherwise-unused (no revocation list for access tokens -- that's
    # what the refresh token is for), but without it two tokens minted for the
    # same user in the same second are byte-identical, which is surprising
    # for something meant to represent a distinct login/refresh event.
    payload = {"sub": str(user_id), "exp": int(time.time()) + minutes * 60, "jti": uuid.uuid4().hex}

    signing_input = (
        f"{_b64url_encode(json.dumps(header).encode())}." f"{_b64url_encode(json.dumps(payload).encode())}"
    )
    signature = hmac.new(settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, signature_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}"
    expected_signature = hmac.new(settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_encode(expected_signature), signature_b64):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("exp", 0) < time.time():
        return None

    # Check the jti against the denied_tokens table.
    if "jti" in payload:
        from app.core.database import SessionLocal
        from app.models.auth_token import DeniedToken
        db = SessionLocal()
        try:
            denied = db.query(DeniedToken).filter(DeniedToken.jti == payload["jti"]).first()
            if denied:
                return None
        finally:
            db.close()

    return payload



def generate_opaque_token() -> str:
    """A random, unguessable token for refresh / password-reset use (not a
    JWT -- these are looked up by hash against a DB row, so they can be
    revoked or marked used)."""

    return secrets.token_urlsafe(32)


def hash_opaque_token(token: str) -> str:
    """SHA-256 is enough here (not PBKDF2): this hashes a high-entropy random
    token for O(1) DB lookup, not a low-entropy user password that needs
    brute-force resistance."""

    return hashlib.sha256(token.encode()).hexdigest()
