"""make_heure_deconnexion_nullable

Revision ID: 7afe9ff106d7
Revises: 88ab363ff8d8
Create Date: 2025-03-28 16:12:10.656174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7afe9ff106d7'
down_revision: Union[str, None] = '88ab363ff8d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
