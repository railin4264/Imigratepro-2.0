"""add case dates, receipt number, and parent case link

Revision ID: a3b2c1d0e9f8
Revises: f2bd413672a4
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b2c1d0e9f8'
down_revision: Union[str, None] = 'f2bd413672a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('cases') as batch_op:
        batch_op.add_column(sa.Column('priority_date', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('filed_date', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('decision_deadline', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('uscis_receipt_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('parent_case_id', sa.Uuid(), nullable=True))
        batch_op.create_index('ix_cases_priority_date', ['priority_date'], unique=False)
        batch_op.create_index('ix_cases_uscis_receipt_number', ['uscis_receipt_number'], unique=False)
        batch_op.create_index('ix_cases_parent_case_id', ['parent_case_id'], unique=False)
        batch_op.create_foreign_key('fk_cases_parent_case_id', 'cases', ['parent_case_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('cases') as batch_op:
        batch_op.drop_constraint('fk_cases_parent_case_id', type_='foreignkey')
        batch_op.drop_index('ix_cases_parent_case_id')
        batch_op.drop_index('ix_cases_uscis_receipt_number')
        batch_op.drop_index('ix_cases_priority_date')
        batch_op.drop_column('parent_case_id')
        batch_op.drop_column('uscis_receipt_number')
        batch_op.drop_column('decision_deadline')
        batch_op.drop_column('filed_date')
        batch_op.drop_column('priority_date')
