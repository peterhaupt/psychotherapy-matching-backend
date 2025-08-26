"""Add reminder_email_id to therapeutenanfrage table

Revision ID: 004_add_reminder_email_to_anfrage
Revises: 003_phase2_patient_updates
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_reminder_email'
down_revision = '003_phase2_patient_updates'
branch_labels = None
depends_on = None


def upgrade():
    """Add reminder_email_id column to therapeutenanfrage table."""
    # Add the new column as nullable integer
    op.add_column(
        'therapeutenanfrage',
        sa.Column('reminder_email_id', sa.Integer(), nullable=True),
        schema='matching_service'
    )
    
    # Create an index on the new column for better query performance
    op.create_index(
        'ix_matching_service_therapeutenanfrage_reminder_email_id',
        'therapeutenanfrage',
        ['reminder_email_id'],
        schema='matching_service'
    )
    
    # Note: We're not adding a foreign key constraint because it would cross service boundaries
    # The reminder_email_id references communication_service.emails.id


def downgrade():
    """Remove reminder_email_id column from therapeutenanfrage table."""
    # Drop the index first
    op.drop_index(
        'ix_matching_service_therapeutenanfrage_reminder_email_id',
        table_name='therapeutenanfrage',
        schema='matching_service'
    )
    
    # Drop the column
    op.drop_column(
        'therapeutenanfrage',
        'reminder_email_id',
        schema='matching_service'
    )