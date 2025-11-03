"""transfer vet and ref snapshot

Revision ID: ab12cd34ef56
Revises: 9a1b2c3d4e5f
Create Date: 2025-11-03 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab12cd34ef56'
down_revision: Union[str, Sequence[str], None] = '9a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transfers') as batch_op:
        batch_op.add_column(sa.Column('vet_value', sa.Numeric(18, 10), nullable=True))
        batch_op.add_column(sa.Column('ref_rate_value', sa.Numeric(18, 10), nullable=True))
        batch_op.add_column(sa.Column('ref_rate_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('ref_rate_source', sa.String(length=32), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('transfers') as batch_op:
        batch_op.drop_column('ref_rate_source')
        batch_op.drop_column('ref_rate_date')
        batch_op.drop_column('ref_rate_value')
        batch_op.drop_column('vet_value')

