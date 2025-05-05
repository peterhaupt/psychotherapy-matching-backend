"""create communication tables

Revision ID: 5dfc91e6b6f9
Revises: 4cfc91d5b5e9
Create Date: 2025-05-05 14:15:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5dfc91e6b6f9'
down_revision: Union[str, None] = '4cfc91d5b5e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create EmailStatus enum type
    email_status = sa.Enum(
        'entwurf', 'in_warteschlange', 'wird_gesendet', 'gesendet', 'fehlgeschlagen',
        name='emailstatus'
    )
    
    # Create emails table
    op.create_table('emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=False),
        sa.Column('sender_email', sa.String(length=255), nullable=False),
        sa.Column('sender_name', sa.String(length=255), nullable=False),
        sa.Column('placement_request_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', email_status, nullable=True),
        sa.Column('queued_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='communication_service'
    )
    
    # Create index on id
    op.create_index(
        op.f('ix_communication_service_emails_id'), 
        'emails', 
        ['id'], 
        unique=False, 
        schema='communication_service'
    )
    
    # Create index on therapist_id for better performance
    op.create_index(
        op.f('ix_communication_service_emails_therapist_id'), 
        'emails', 
        ['therapist_id'], 
        unique=False, 
        schema='communication_service'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the indexes
    op.drop_index(
        op.f('ix_communication_service_emails_therapist_id'), 
        table_name='emails', 
        schema='communication_service'
    )
    op.drop_index(
        op.f('ix_communication_service_emails_id'), 
        table_name='emails', 
        schema='communication_service'
    )
    
    # Drop the table
    op.drop_table('emails', schema='communication_service')
    
    # Drop the enum
    sa.Enum(name='emailstatus').drop(op.get_bind())