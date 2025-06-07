"""rename potentially available fields to german

Revision ID: ecfc00g3k4k4
Revises: dcfc99f2h3j3
Create Date: 2025-05-22 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ecfc00g3k4k4'
down_revision: Union[str, None] = 'dcfc99f2h3j3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename potentially_available fields to German."""
    
    # Rename potentially_available to potenziell_verfuegbar
    op.alter_column('therapists', 'potentially_available',
                    new_column_name='potenziell_verfuegbar',
                    schema='therapist_service')
    
    # Rename potentially_available_notes to potenziell_verfuegbar_notizen
    op.alter_column('therapists', 'potentially_available_notes',
                    new_column_name='potenziell_verfuegbar_notizen',
                    schema='therapist_service')


def downgrade() -> None:
    """Rename fields back to English."""
    
    # Rename back to English
    op.alter_column('therapists', 'potenziell_verfuegbar',
                    new_column_name='potentially_available',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'potenziell_verfuegbar_notizen',
                    new_column_name='potentially_available_notes',
                    schema='therapist_service')
