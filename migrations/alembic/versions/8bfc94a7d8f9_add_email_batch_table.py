"""add email batch table

Revision ID: 8bfc94a7d8f9
Revises: 7bfc93a7c8e9
Create Date: 2025-05-07 14:45:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8bfc94a7d8f9'
down_revision: Union[str, None] = '7bfc93a7c8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with email batch table and updated email fields."""
    # 1. Add new columns to the emails table
    op.add_column('emails', 
                  sa.Column('batch_id', sa.String(50)),
                  schema='communication_service')
                  
    op.add_column('emails', 
                  sa.Column('response_received', sa.Boolean(), 
                            nullable=False, server_default='false'),
                  schema='communication_service')
                  
    op.add_column('emails', 
                  sa.Column('response_date', sa.DateTime()),
                  schema='communication_service')
                  
    op.add_column('emails', 
                  sa.Column('response_content', sa.Text()),
                  schema='communication_service')
                  
    op.add_column('emails', 
                  sa.Column('follow_up_required', sa.Boolean(), 
                            nullable=False, server_default='false'),
                  schema='communication_service')
                  
    op.add_column('emails', 
                  sa.Column('follow_up_notes', sa.Text()),
                  schema='communication_service')
    
    # 2. Create email_batches table
    op.create_table('email_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('placement_request_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=True),
        sa.Column('included', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('response_outcome', sa.String(50), nullable=True),
        sa.Column('response_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), 
                 server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['communication_service.emails.id'], 
                              ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['placement_request_id'], 
                              ['matching_service.placement_requests.id'], 
                              ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='communication_service'
    )
    
    # 3. Create indexes for email_batches
    op.create_index('idx_email_batches_email_id', 'email_batches', ['email_id'], 
                   schema='communication_service')
    op.create_index('idx_email_batches_placement_request_id', 'email_batches', 
                   ['placement_request_id'], schema='communication_service')
    
    # 4. Create a unique constraint to prevent duplicates
    op.create_unique_constraint('uq_email_batches_email_placement', 
                              'email_batches', ['email_id', 'placement_request_id'],
                              schema='communication_service')


def downgrade() -> None:
    """Downgrade schema by removing email batch table and added columns."""
    # 1. Remove unique constraint
    op.drop_constraint('uq_email_batches_email_placement', 'email_batches',
                     schema='communication_service')
                     
    # 2. Remove indexes
    op.drop_index('idx_email_batches_placement_request_id', table_name='email_batches',
                schema='communication_service')
    op.drop_index('idx_email_batches_email_id', table_name='email_batches',
                schema='communication_service')
                
    # 3. Drop the email_batches table
    op.drop_table('email_batches', schema='communication_service')
    
    # 4. Remove the added columns from emails table
    op.drop_column('emails', 'follow_up_notes', schema='communication_service')
    op.drop_column('emails', 'follow_up_required', schema='communication_service')
    op.drop_column('emails', 'response_content', schema='communication_service')
    op.drop_column('emails', 'response_date', schema='communication_service')
    op.drop_column('emails', 'response_received', schema='communication_service')
    op.drop_column('emails', 'batch_id', schema='communication_service')