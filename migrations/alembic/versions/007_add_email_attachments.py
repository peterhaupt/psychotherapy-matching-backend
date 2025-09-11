"""Add attachments column to emails table for PDF support

Revision ID: 007_add_email_attachments
Revises: 006_remove_kontaktanfrage
Create Date: 2025-01-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007_add_email_attachments'
down_revision: Union[str, None] = '006_remove_kontaktanfrage'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add attachments column to emails table for PDF attachment support."""
    print("Adding attachments column to emails table...")
    
    # Add the new JSONB column for storing attachment file paths
    op.add_column(
        'emails',
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema='communication_service'
    )
    
    # Create an index on the new column for better query performance when filtering by attachments
    op.create_index(
        'ix_communication_service_emails_attachments',
        'emails',
        ['attachments'],
        schema='communication_service',
        postgresql_using='gin'  # GIN index is optimal for JSONB columns
    )
    
    print("Successfully added attachments column to emails table")


def downgrade() -> None:
    """Remove attachments column from emails table."""
    print("Removing attachments column from emails table...")
    
    # Drop the index first
    op.drop_index(
        'ix_communication_service_emails_attachments',
        table_name='emails',
        schema='communication_service'
    )
    
    # Drop the column
    op.drop_column(
        'emails',
        'attachments',
        schema='communication_service'
    )
    
    print("Successfully removed attachments column from emails table")
