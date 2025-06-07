"""remove unused therapist date fields

Revision ID: ccfc98e1g2i2
Revises: bcfc97d0f1h1
Create Date: 2025-05-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ccfc98e1g2i2'
down_revision: Union[str, None] = 'bcfc97d0f1h1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused therapist date fields that are not part of the bundle system."""
    
    # Drop the unused date columns
    op.drop_column('therapists', 'freie_einzeltherapieplaetze_ab', schema='therapist_service')
    op.drop_column('therapists', 'freie_gruppentherapieplaetze_ab', schema='therapist_service')


def downgrade() -> None:
    """Re-add the removed date fields."""
    
    # Re-add the columns
    op.add_column('therapists', 
                  sa.Column('freie_einzeltherapieplaetze_ab', sa.Date(), nullable=True),
                  schema='therapist_service')
    
    op.add_column('therapists', 
                  sa.Column('freie_gruppentherapieplaetze_ab', sa.Date(), nullable=True),
                  schema='therapist_service')