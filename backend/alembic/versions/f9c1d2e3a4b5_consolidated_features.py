"""consolidated feature migration: form category, notification scoping, case dates/parent

Revision ID: f9c1d2e3a4b5
Revises: 67ad1d579740, 754c137df36a, cbcf09298bb7
Create Date: 2026-07-22 00:00:00.000000

Combines three feature branches (form category, notification recipient
scoping, case key dates + parent link) into a single head so Alembic has
exactly one head after the parallel worktrees were merged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9c1d2e3a4b5'
down_revision: Union[tuple, None] = ('67ad1d579740', '754c137df36a', 'cbcf09298bb7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Codes that map to a non-default category; everything else stays 'general'.
_CATEGORY_MAP = {
    'I-130': 'family', 'I-485': 'family', 'I-864': 'family', 'I-134': 'family',
    'I-131': 'family', 'I-693': 'family', 'I-751': 'family',
    'I-140': 'employment', 'I-129': 'employment', 'I-129F': 'employment',
    'I-589': 'asylum',
    'N-400': 'naturalization', 'N-600': 'naturalization', 'N-426': 'naturalization',
    'I-765': 'adjustment', 'I-539': 'adjustment', 'I-90': 'adjustment',
}


def upgrade() -> None:
    bind = op.get_bind()

    # --- FormTemplate.category ---
    if bind.dialect.name == 'postgresql':
        op.execute(
            "DO $$ BEGIN "
            "  CREATE TYPE formcategory AS ENUM "
            "  ('family','employment','asylum','naturalization','adjustment','general','other'); "
            "EXCEPTION WHEN duplicate_object THEN null; END $$"
        )
    category_enum = sa.Enum(
        'family', 'employment', 'asylum', 'naturalization', 'adjustment', 'general', 'other',
        name='formcategory',
        create_type=False,
    )
    op.add_column(
        'form_templates',
        sa.Column('category', category_enum, nullable=False, server_default='general'),
    )
    op.create_index('ix_form_templates_category', 'form_templates', ['category'], unique=False)
    form_templates = sa.table(
        'form_templates',
        sa.column('code', sa.String),
        sa.column('category', sa.String),
    )
    for code, category in _CATEGORY_MAP.items():
        op.execute(
            form_templates.update()
            .where(form_templates.c.code == code)
            .values(category=category)
        )

    # --- Notification recipient scoping ---
    op.add_column('notifications', sa.Column('recipient_user_id', sa.Uuid(), nullable=True))
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
    op.add_column('notifications', sa.Column('is_global', sa.Boolean(), nullable=False, server_default=sa.false()))
    if bind.dialect.name == 'postgresql':
        op.create_foreign_key(
            'fk_notifications_recipient_user_id',
            'notifications', 'users',
            ['recipient_user_id'], ['id'],
        )
    op.create_index(op.f('ix_notifications_recipient_user_id'), 'notifications', ['recipient_user_id'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_role'), 'notifications', ['recipient_role'], unique=False)

    # --- Case key dates + parent link ---
    op.add_column('cases', sa.Column('priority_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cases', sa.Column('filed_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cases', sa.Column('decision_deadline', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cases', sa.Column('uscis_receipt_number', sa.String(20), nullable=True))
    op.add_column('cases', sa.Column('parent_case_id', sa.Uuid(), nullable=True))
    op.create_index('ix_cases_priority_date', 'cases', ['priority_date'], unique=False)
    op.create_index('ix_cases_uscis_receipt_number', 'cases', ['uscis_receipt_number'], unique=False)
    op.create_index('ix_cases_parent_case_id', 'cases', ['parent_case_id'], unique=False)
    if bind.dialect.name == 'postgresql':
        op.create_foreign_key('fk_cases_parent_case_id', 'cases', 'cases', ['parent_case_id'], ['id'])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index('ix_cases_parent_case_id', table_name='cases')
    op.drop_index('ix_cases_uscis_receipt_number', table_name='cases')
    op.drop_index('ix_cases_priority_date', table_name='cases')
    if bind.dialect.name == 'postgresql':
        op.drop_constraint('fk_cases_parent_case_id', 'cases', type_='foreignkey')
    op.drop_column('cases', 'parent_case_id')
    op.drop_column('cases', 'uscis_receipt_number')
    op.drop_column('cases', 'decision_deadline')
    op.drop_column('cases', 'filed_date')
    op.drop_column('cases', 'priority_date')

    op.drop_index(op.f('ix_notifications_recipient_role'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_recipient_user_id'), table_name='notifications')
    if bind.dialect.name == 'postgresql':
        op.drop_constraint('fk_notifications_recipient_user_id', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'is_global')
    op.drop_column('notifications', 'recipient_role')
    op.drop_column('notifications', 'recipient_user_id')

    op.drop_index('ix_form_templates_category', table_name='form_templates')
    op.drop_column('form_templates', 'category')
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS formcategory')
