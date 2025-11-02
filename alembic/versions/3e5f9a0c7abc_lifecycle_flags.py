"""lifecycle flags

Revision ID: 3e5f9a0c7abc
Revises: 1f2a3b4c5d6e
Create Date: 2025-11-02 04:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e5f9a0c7abc'
down_revision: Union[str, Sequence[str], None] = '1f2a3b4c5d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # accounts.status
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=10), nullable=False, server_default=sa.text("'ACTIVE'")))

    # categories.active
    with op.batch_alter_table('categories') as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()))

    # transactions.voided
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.add_column(sa.Column('voided', sa.Boolean(), nullable=False, server_default=sa.false()))

    # transfers.voided
    with op.batch_alter_table('transfers') as batch_op:
        batch_op.add_column(sa.Column('voided', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table('transfers') as batch_op:
        batch_op.drop_column('voided')
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_column('voided')
    with op.batch_alter_table('categories') as batch_op:
        batch_op.drop_column('active')
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.drop_column('status')

