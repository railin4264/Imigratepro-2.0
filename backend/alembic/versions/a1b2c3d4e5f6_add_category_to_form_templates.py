"""add category to form_templates

Revision ID: a1b2c3d4e5f6
Revises: 67ad1d579740, cbcf09298bb7, 754c137df36a
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[tuple, None] = ('67ad1d579740', 'cbcf09298bb7', '754c137df36a')
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

    # PostgreSQL needs the enum type created before the column can reference it.
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
        create_type=False,  # we created it above for Postgres; SQLite ignores it
    )
    # server_default backfills existing rows for the new NOT NULL column.
    op.add_column(
        'form_templates',
        sa.Column('category', category_enum, nullable=False, server_default='general'),
    )
    op.create_index('ix_form_templates_category', 'form_templates', ['category'], unique=False)

    # Backfill known codes; safe to re-run (UPDATE is a no-op when value already matches).
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


def downgrade() -> None:
    op.drop_index('ix_form_templates_category', table_name='form_templates')
    op.drop_column('form_templates', 'category')
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS formcategory')
