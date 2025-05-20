"""add firebase_token to tablettes table

Revision ID: a9cba29009dd
Revises: 17e10068af2b
Create Date: 2025-04-07 11:47:40.889511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9cba29009dd'
down_revision: Union[str, None] = '17e10068af2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
