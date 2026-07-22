"""add recipient scoping to notifications

Revision ID: a1b2c3d4e5f6
Revises: cbcf09298bb7
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, tuple] = ('cbcf09298bb7', '67ad1d579740', '754c137df36a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        'notifications',
        sa.Column('recipient_user_id', sa.Uuid(), nullable=True),
    )
    op.add_column(
        'notifications',
        sa.Column(
            'recipient_role',
            sa.Enum(
                'OWNER', 'ADMIN', 'ATTORNEY', 'PARALEGAL',
                'LEGAL_ASSISTANT', 'INTAKE', 'BILLING', 'CONTRACT_ATTORNEY',
                name='userrole',
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        'notifications',
        sa.Column('is_global', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    if bind.dialect.name == 'postgresql':
        op.create_foreign_key(
            'fk_notifications_recipient_user_id',
            'notifications', 'users',
            ['recipient_user_id'], ['id'],
        )

    op.create_index(op.f('ix_notifications_recipient_user_id'), 'notifications', ['recipient_user_id'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_role'), 'notifications', ['recipient_role'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_recipient_role'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_recipient_user_id'), table_name='notifications')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.drop_constraint('fk_notifications_recipient_user_id', 'notifications', type_='foreignkey')

    op.drop_column('notifications', 'is_global')
    op.drop_column('notifications', 'recipient_role')
    op.drop_column('notifications', 'recipient_user_id')
