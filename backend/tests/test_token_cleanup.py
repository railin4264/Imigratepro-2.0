import uuid
from datetime import datetime, timedelta, timezone

from app.models.auth_token import PasswordResetToken, RefreshToken
from app.services.token_cleanup import cleanup_expired_tokens


def test_cleanup_deletes_long_expired_tokens_but_keeps_recent_ones(db_session, admin_user):
    now = datetime.now(timezone.utc)

    long_expired = RefreshToken(
        user_id=admin_user.id, token_hash=uuid.uuid4().hex, expires_at=now - timedelta(days=30)
    )
    recently_expired = RefreshToken(
        user_id=admin_user.id, token_hash=uuid.uuid4().hex, expires_at=now - timedelta(hours=1)
    )
    still_valid = RefreshToken(
        user_id=admin_user.id, token_hash=uuid.uuid4().hex, expires_at=now + timedelta(days=10)
    )
    old_reset_token = PasswordResetToken(
        user_id=admin_user.id, token_hash=uuid.uuid4().hex, expires_at=now - timedelta(days=30)
    )
    db_session.add_all([long_expired, recently_expired, still_valid, old_reset_token])
    db_session.commit()
    # Capture IDs before cleanup's own commit expires these ORM instances.
    long_expired_id, recently_expired_id, still_valid_id = long_expired.id, recently_expired.id, still_valid.id

    result = cleanup_expired_tokens(db_session)
    assert result["refresh_tokens_deleted"] == 1
    assert result["reset_tokens_deleted"] == 1

    remaining_refresh = {t.id for t in db_session.query(RefreshToken).all()}
    assert long_expired_id not in remaining_refresh
    assert recently_expired_id in remaining_refresh
    assert still_valid_id in remaining_refresh

    assert db_session.query(PasswordResetToken).count() == 0


def test_cleanup_deletes_long_revoked_and_used_tokens(db_session, admin_user):
    now = datetime.now(timezone.utc)

    long_revoked = RefreshToken(
        user_id=admin_user.id,
        token_hash=uuid.uuid4().hex,
        expires_at=now + timedelta(days=10),
        revoked_at=now - timedelta(days=30),
    )
    long_used_reset = PasswordResetToken(
        user_id=admin_user.id,
        token_hash=uuid.uuid4().hex,
        expires_at=now + timedelta(hours=1),
        used_at=now - timedelta(days=30),
    )
    db_session.add_all([long_revoked, long_used_reset])
    db_session.commit()

    result = cleanup_expired_tokens(db_session)
    assert result["refresh_tokens_deleted"] == 1
    assert result["reset_tokens_deleted"] == 1
