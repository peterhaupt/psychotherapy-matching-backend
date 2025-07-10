"""Add therapeutenanfrage_id to phone_calls table

Revision ID: 002_therapeutenanfrage_id
Revises: 001_initial_setup
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_therapeutenanfrage_id'
down_revision = '001_initial_setup' 
branch_labels = None
depends_on = None


def upgrade():
    """Add therapeutenanfrage_id column to telefonanrufe table."""
    # Add the new column as nullable integer
    op.add_column(
        'telefonanrufe',
        sa.Column('therapeutenanfrage_id', sa.Integer(), nullable=True),
        schema='communication_service'
    )
    
    # Create an index on the new column for better query performance
    op.create_index(
        'ix_communication_service_telefonanrufe_therapeutenanfrage_id',
        'telefonanrufe',
        ['therapeutenanfrage_id'],
        schema='communication_service'
    )
    
    # Note: We're not adding a foreign key constraint because it would cross service boundaries
    # The matching_service.therapeutenanfrage table is in a different service


def downgrade():
    """Remove therapeutenanfrage_id column from telefonanrufe table."""
    # Drop the index first
    op.drop_index(
        'ix_communication_service_telefonanrufe_therapeutenanfrage_id',
        table_name='telefonanrufe',
        schema='communication_service'
    )
    
    # Drop the column
    op.drop_column(
        'telefonanrufe',
        'therapeutenanfrage_id',
        schema='communication_service'
    )