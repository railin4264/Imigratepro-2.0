"""Create the first admin login so the app isn't locked out once every
endpoint requires authentication. Only creates a user if no user in the
database has a password set yet -- safe to re-run.

Run with: ./.venv/Scripts/python.exe -m app.seed_admin
Credentials come from SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD env vars, or
default to admin@migratepro.local / changeme123 (change it after first login).
"""

import os

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

DEFAULT_EMAIL = "admin@migratepro.local"
DEFAULT_PASSWORD = "changeme123"


def seed() -> None:
    email = os.environ.get("SEED_ADMIN_EMAIL", DEFAULT_EMAIL)
    password = os.environ.get("SEED_ADMIN_PASSWORD", DEFAULT_PASSWORD)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.hashed_password.is_not(None)).first():
            print("An account with a password already exists -- skipping.")
            return

        user = db.query(User).filter_by(email=email).one_or_none()
        if user is None:
            user = User(full_name="Admin", email=email, role=UserRole.ADMIN)
            db.add(user)
        else:
            user.role = UserRole.ADMIN

        user.hashed_password = hash_password(password)
        db.commit()
        print(f"Admin account ready: {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
