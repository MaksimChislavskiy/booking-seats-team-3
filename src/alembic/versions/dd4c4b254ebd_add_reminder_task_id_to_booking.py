"""add reminder_task_id to booking

Revision ID: dd4c4b254ebd
Revises: 72c9d11a8d11
Create Date: 2026-01-12 23:27:47.246567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd4c4b254ebd'
down_revision: Union[str, Sequence[str], None] = '72c9d11a8d11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'booking',
        sa.Column('reminder_task_id', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('booking', 'reminder_task_id')
