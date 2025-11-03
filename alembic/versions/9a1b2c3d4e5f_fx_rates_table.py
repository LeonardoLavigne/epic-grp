"""fx_rates table

Revision ID: 9a1b2c3d4e5f
Revises: 1f2a3b4c5d6e
Create Date: 2025-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '3e5f9a0c7abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'fx_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('base', sa.String(length=3), nullable=False),
        sa.Column('quote', sa.String(length=3), nullable=False),
        sa.Column('rate_value', sa.Numeric(18, 10), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'base', 'quote', name='uq_fx_rates_date_base_quote')
    )
    op.create_index(op.f('ix_fx_rates_date'), 'fx_rates', ['date'], unique=False)
    op.create_index(op.f('ix_fx_rates_base'), 'fx_rates', ['base'], unique=False)
    op.create_index(op.f('ix_fx_rates_quote'), 'fx_rates', ['quote'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_fx_rates_quote'), table_name='fx_rates')
    op.drop_index(op.f('ix_fx_rates_base'), table_name='fx_rates')
    op.drop_index(op.f('ix_fx_rates_date'), table_name='fx_rates')
    op.drop_table('fx_rates')
