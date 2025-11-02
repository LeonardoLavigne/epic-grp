"""transfers

Revision ID: 1f2a3b4c5d6e
Revises: 7b31df0d3abc
Create Date: 2025-11-02 04:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f2a3b4c5d6e'
down_revision: Union[str, Sequence[str], None] = '7b31df0d3abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('src_account_id', sa.Integer(), nullable=False),
        sa.Column('dst_account_id', sa.Integer(), nullable=False),
        sa.Column('src_amount_cents', sa.BigInteger(), nullable=False),
        sa.Column('dst_amount_cents', sa.BigInteger(), nullable=False),
        sa.Column('rate_base', sa.String(length=3), nullable=False),
        sa.Column('rate_quote', sa.String(length=3), nullable=False),
        sa.Column('rate_value', sa.Numeric(18, 10), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['src_account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['dst_account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add transfer_id to transactions (use batch for SQLite compatibility)
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.add_column(sa.Column('transfer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_transactions_transfer', 'transfers', ['transfer_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_constraint('fk_transactions_transfer', type_='foreignkey')
        batch_op.drop_column('transfer_id')
    op.drop_table('transfers')
