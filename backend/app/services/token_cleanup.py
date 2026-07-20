"""Deletes refresh/password-reset tokens that are no longer useful for
anything -- expired, revoked, or already used. Nothing breaks if this never
runs (an expired/revoked token is already rejected by app/api/v1/endpoints/
auth.py regardless), it just keeps these tables from growing forever. Run by
the scheduler (app/services/scheduler.py) alongside the reminder/overdue
sweeps."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.auth_token import PasswordResetToken, RefreshToken

# Keep a short grace window past expiry/use rather than deleting the instant
# a token becomes unusable -- useful if you're ever staring at the table
# trying to understand what happened to a session.
_RETENTION = timedelta(days=7)


def cleanup_expired_tokens(db: Session) -> dict:
    cutoff = datetime.now(timezone.utc) - _RETENTION

    refresh_deleted = (
        db.query(RefreshToken)
        .filter(
            (RefreshToken.expires_at < cutoff) | (RefreshToken.revoked_at.is_not(None) & (RefreshToken.revoked_at < cutoff))
        )
        .delete(synchronize_session=False)
    )
    reset_deleted = (
        db.query(PasswordResetToken)
        .filter(
            (PasswordResetToken.expires_at < cutoff)
            | (PasswordResetToken.used_at.is_not(None) & (PasswordResetToken.used_at < cutoff))
        )
        .delete(synchronize_session=False)
    )

    db.commit()
    return {"refresh_tokens_deleted": refresh_deleted, "reset_tokens_deleted": reset_deleted}
