"""update oauth and add gmail account

Revision ID: ea8d43315a18
Revises: 68e5a149bc98
Create Date: 2024-12-14 23:33:42.504083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea8d43315a18'
down_revision: Union[str, None] = '68e5a149bc98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gmail_account',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('oauth_credentials_id', sa.Uuid(), nullable=False),
    sa.Column('watch_history_id', sa.String(length=255), nullable=True),
    sa.Column('watch_expiration', sa.DateTime(), nullable=True),
    sa.Column('watch_topic_name', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['oauth_credentials_id'], ['o_auth_credentials.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('oauth_credentials_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('gmail_account')
    # ### end Alembic commands ###
