"""Add vermittelter_therapeut_id to platzsuche table

Revision ID: 005_vermittelter_therapeut
Revises: 004_add_reminder_email
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_vermittelter_therapeut'
down_revision = '004_add_reminder_email'
branch_labels = None
depends_on = None


def upgrade():
    """Add vermittelter_therapeut_id column to platzsuche table."""
    print("Adding vermittelter_therapeut_id to platzsuche table...")
    
    # Add the new column as nullable integer
    op.add_column(
        'platzsuche',
        sa.Column('vermittelter_therapeut_id', sa.Integer(), nullable=True),
        schema='matching_service'
    )
    
    # Create an index on the new column for better query performance
    op.create_index(
        'ix_matching_service_platzsuche_vermittelter_therapeut_id',
        'platzsuche',
        ['vermittelter_therapeut_id'],
        schema='matching_service'
    )
    
    # Note: We're not adding a foreign key constraint because it would cross service boundaries
    # The vermittelter_therapeut_id references therapist_service.therapeuten.id
    
    print("Successfully added vermittelter_therapeut_id to platzsuche table")


def downgrade():
    """Remove vermittelter_therapeut_id column from platzsuche table."""
    print("Removing vermittelter_therapeut_id from platzsuche table...")
    
    # Drop the index first
    op.drop_index(
        'ix_matching_service_platzsuche_vermittelter_therapeut_id',
        table_name='platzsuche',
        schema='matching_service'
    )
    
    # Drop the column
    op.drop_column(
        'platzsuche',
        'vermittelter_therapeut_id',
        schema='matching_service'
    )
    
    print("Successfully removed vermittelter_therapeut_id from platzsuche table")