"""add changes

Revision ID: 6881f4fb9282
Revises: 2c149a758cb2
Create Date: 2025-01-20 10:59:01.220439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6881f4fb9282'
down_revision: Union[str, None] = '2c149a758cb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('account', sa.Column('account_name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('account', 'account_name')
    # ### end Alembic commands ###
