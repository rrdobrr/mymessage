"""create read_status_table CORRECTED

Revision ID: 4343cfea8d69
Revises: 80dea67eac3e
Create Date: 2025-04-07 06:01:19.240253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4343cfea8d69'
down_revision: Union[str, None] = '80dea67eac3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('messages', 'read_by')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('read_by', postgresql.ARRAY(sa.INTEGER()), server_default=sa.text("'{}'::integer[]"), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
