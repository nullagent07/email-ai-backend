"""add status in email thread

Revision ID: 68e5a149bc98
Revises: cf0b62c5f377
Create Date: 2024-12-13 00:44:03.662509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '68e5a149bc98'
down_revision: Union[str, None] = 'cf0b62c5f377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    op.execute("CREATE TYPE emailthreadstatus AS ENUM ('active', 'stopped')")
    
    # Add column using the created enum type
    op.add_column('email_threads', sa.Column('status', postgresql.ENUM('active', 'stopped', name='emailthreadstatus', create_type=False), server_default='stopped', nullable=False))


def downgrade() -> None:
    # Drop column first
    op.drop_column('email_threads', 'status')
    
    # Drop enum type
    op.execute("DROP TYPE emailthreadstatus")
