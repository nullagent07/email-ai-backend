"""add user_id in gmail_account

Revision ID: 6053dbc63630
Revises: ea8d43315a18
Create Date: 2024-12-17 23:01:36.246523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6053dbc63630'
down_revision: Union[str, None] = 'ea8d43315a18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('gmail_account', sa.Column('user_id', sa.Uuid(), nullable=False))
    op.create_foreign_key(None, 'gmail_account', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'gmail_account', type_='foreignkey')
    op.drop_column('gmail_account', 'user_id')
    # ### end Alembic commands ###
