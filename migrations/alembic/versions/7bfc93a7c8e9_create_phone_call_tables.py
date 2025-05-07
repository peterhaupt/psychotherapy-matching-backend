"""create phone call tables

Revision ID: 7bfc93a7c8e9
Revises: 6fbc92a7b7e9
Create Date: 2025-05-07 11:30:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7bfc93a7c8e9'
down_revision: Union[str, None] = '6fbc92a7b7e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create phone call and phone call batch tables."""
    # We'll use server_default for enum values instead of creating the enum type
    # PostgreSQL will automatically create the enum type if it doesn't exist
    
    # Create phone_calls table
    op.create_table('phone_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.Time(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('actual_time', sa.Time(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='scheduled'),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('retry_after', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='communication_service'
    )
    
    # Create indexes for phone_calls
    op.create_index('idx_phone_calls_therapist_id', 'phone_calls', ['therapist_id'], 
                   schema='communication_service')
    op.create_index('idx_phone_calls_scheduled_date', 'phone_calls', ['scheduled_date'], 
                   schema='communication_service')
    op.create_index('idx_phone_calls_status', 'phone_calls', ['status'], 
                   schema='communication_service')
    
    # Create phone_call_batches table
    op.create_table('phone_call_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_call_id', sa.Integer(), nullable=False),
        sa.Column('placement_request_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('discussed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['phone_call_id'], 
                               ['communication_service.phone_calls.id'], 
                               ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['placement_request_id'], 
                               ['matching_service.placement_requests.id'], 
                               ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_call_id', 'placement_request_id'),
        schema='communication_service'
    )
    
    # Create indexes for phone_call_batches
    op.create_index('idx_phone_call_batches_phone_call_id', 'phone_call_batches', 
                   ['phone_call_id'], schema='communication_service')
    op.create_index('idx_phone_call_batches_placement_request_id', 'phone_call_batches', 
                   ['placement_request_id'], schema='communication_service')


def downgrade() -> None:
    """Drop phone call and phone call batch tables."""
    # Drop the indexes and tables in reverse order
    op.drop_index('idx_phone_call_batches_placement_request_id', 
                 table_name='phone_call_batches', schema='communication_service')
    op.drop_index('idx_phone_call_batches_phone_call_id', 
                 table_name='phone_call_batches', schema='communication_service')
    op.drop_table('phone_call_batches', schema='communication_service')
    
    op.drop_index('idx_phone_calls_status', 
                 table_name='phone_calls', schema='communication_service')
    op.drop_index('idx_phone_calls_scheduled_date', 
                 table_name='phone_calls', schema='communication_service')
    op.drop_index('idx_phone_calls_therapist_id', 
                 table_name='phone_calls', schema='communication_service')
    op.drop_table('phone_calls', schema='communication_service')