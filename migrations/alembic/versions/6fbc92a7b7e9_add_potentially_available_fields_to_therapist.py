"""add potentially available fields to therapist

Revision ID: 6fbc92a7b7e9
Revises: 5dfc91e6b6f9
Create Date: 2025-05-07 10:15:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6fbc92a7b7e9'
down_revision: Union[str, None] = '5dfc91e6b6f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add potentially available fields to therapist table."""
    # Add potentially_available column with default value of False
    op.add_column('therapists', 
                  sa.Column('potentially_available', sa.Boolean(), 
                           server_default='false'),
                  schema='therapist_service')
    
    # Add potentially_available_notes column
    op.add_column('therapists',
                  sa.Column('potentially_available_notes', sa.Text()),
                  schema='therapist_service')


def downgrade() -> None:
    """Remove potentially available fields from therapist table."""
    # Drop the columns in reverse order
    op.drop_column('therapists', 'potentially_available_notes', 
                  schema='therapist_service')
    op.drop_column('therapists', 'potentially_available', 
                  schema='therapist_service')