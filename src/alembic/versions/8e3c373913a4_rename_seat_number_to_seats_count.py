"""rename seat_number to seats_count

Revision ID: 8e3c373913a4
Revises: 2fbff75b0d36
Create Date: 2026-01-09 03:31:35.026691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e3c373913a4'
down_revision: Union[str, Sequence[str], None] = '2fbff75b0d36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'table',            # имя таблицы
        'seat_number',      # старое имя колонки
        new_column_name='seats_count'  # новое имя
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'table',
        'seats_count',
        new_column_name='seat_number'
    )
