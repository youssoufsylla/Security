"""make_heure_deconnexion_nullable

Revision ID: 17e10068af2b
Revises: 7afe9ff106d7
Create Date: 2025-03-28 16:17:27.151133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17e10068af2b'
down_revision: Union[str, None] = '7afe9ff106d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
