"""add deadline reminder fields to cases and rfes

Revision ID: d3e5a6f7b8c9
Revises: f9c1d2e3a4b5
Create Date: 2026-07-22 00:00:00.000000

Backs the case decision_deadline / RFE response_due_date reminder sweeps
(app/services/reminders.py) with a per-row sent flag, mirroring
Appointment.reminder_sent.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e5a6f7b8c9'
down_revision: Union[str, None] = 'f9c1d2e3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'cases',
        sa.Column('deadline_reminder_sent', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'rfes',
        sa.Column('deadline_reminder_sent', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # SQLite stores Enum columns as a plain VARCHAR (no DB-level constraint),
    # so the new NotificationType members just work there. Postgres uses a
    # real enum type that needs each new value added explicitly -- ADD VALUE
    # can't run inside the same transaction it's used in, which is fine since
    # we don't insert any of these values here. Same pattern as
    # 292911351f78_add_billing_invoices_and_payments.py.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for value in ("case_deadline_reminder", "rfe_deadline_reminder"):
            op.execute(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    op.drop_column('rfes', 'deadline_reminder_sent')
    op.drop_column('cases', 'deadline_reminder_sent')
