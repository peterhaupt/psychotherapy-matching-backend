"""add therapist group therapy preference

Revision ID: dcfc99f2h3j3
Revises: ccfc98e1g2i2
Create Date: 2025-05-21 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dcfc99f2h3j3'
down_revision: Union[str, None] = 'ccfc98e1g2i2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add group therapy preference field to therapist bundle preferences."""
    
    # Add bevorzugt_gruppentherapie column
    op.add_column('therapists', 
                  sa.Column('bevorzugt_gruppentherapie', sa.Boolean(), 
                           nullable=False, server_default='false'),
                  schema='therapist_service')


def downgrade() -> None:
    """Remove group therapy preference field."""
    
    # Drop the column
    op.drop_column('therapists', 'bevorzugt_gruppentherapie', 
                  schema='therapist_service')