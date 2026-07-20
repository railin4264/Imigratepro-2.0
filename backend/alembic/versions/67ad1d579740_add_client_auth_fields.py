"""add_client_auth_fields

Revision ID: 67ad1d579740
Revises: 36635b30dde7
Create Date: 2026-07-20 18:43:55.795106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67ad1d579740'
down_revision: Union[str, None] = '36635b30dde7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Add columns to clients table conditionally
    clients_columns = [c['name'] for c in inspector.get_columns('clients')]
    if 'hashed_password' not in clients_columns:
        op.add_column('clients', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    if 'failed_login_attempts' not in clients_columns:
        op.add_column('clients', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    if 'locked_until' not in clients_columns:
        op.add_column('clients', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    # 2. Batch alter password_reset_tokens conditionally
    pr_columns = [c['name'] for c in inspector.get_columns('password_reset_tokens')]
    if 'client_id' not in pr_columns:
        with op.batch_alter_table('password_reset_tokens') as batch_op:
            batch_op.add_column(sa.Column('client_id', sa.Uuid(), nullable=True))
            batch_op.alter_column('user_id', existing_type=sa.Uuid(), nullable=True)
            batch_op.create_index('ix_password_reset_tokens_client_id', ['client_id'], unique=False)
            batch_op.create_foreign_key('fk_password_reset_tokens_client', 'clients', ['client_id'], ['id'], ondelete='CASCADE')

    # 3. Batch alter refresh_tokens conditionally
    rt_columns = [c['name'] for c in inspector.get_columns('refresh_tokens')]
    if 'client_id' not in rt_columns:
        with op.batch_alter_table('refresh_tokens') as batch_op:
            batch_op.add_column(sa.Column('client_id', sa.Uuid(), nullable=True))
            batch_op.alter_column('user_id', existing_type=sa.Uuid(), nullable=True)
            batch_op.create_index('ix_refresh_tokens_client_id', ['client_id'], unique=False)
            batch_op.create_foreign_key('fk_refresh_tokens_client', 'clients', ['client_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # 1. Downgrade refresh_tokens
    with op.batch_alter_table('refresh_tokens') as batch_op:
        batch_op.drop_index('ix_refresh_tokens_client_id')
        batch_op.drop_column('client_id')
        batch_op.alter_column('user_id', existing_type=sa.Uuid(), nullable=False)

    # 2. Downgrade password_reset_tokens
    with op.batch_alter_table('password_reset_tokens') as batch_op:
        batch_op.drop_index('ix_password_reset_tokens_client_id')
        batch_op.drop_column('client_id')
        batch_op.alter_column('user_id', existing_type=sa.Uuid(), nullable=False)

    # 3. Downgrade clients table
    op.drop_column('clients', 'locked_until')
    op.drop_column('clients', 'failed_login_attempts')
    op.drop_column('clients', 'hashed_password')
