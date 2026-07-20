"""add_new_roles_to_userrole

Revision ID: cbcf09298bb7
Revises: 36635b30dde7
Create Date: 2026-07-20 18:37:13.584896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbcf09298bb7'
down_revision: Union[str, None] = '36635b30dde7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for value in ('OWNER', 'LEGAL_ASSISTANT', 'INTAKE', 'BILLING', 'CONTRACT_ATTORNEY'):
            op.execute(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres can't drop individual enum values without recreating the type;
    # left in place on downgrade (harmless -- unused values are never written).
    pass
