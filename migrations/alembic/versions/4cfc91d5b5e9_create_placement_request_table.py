"""create placement request table

Revision ID: 4cfc91d5b5e9
Revises: 3bfc91c5b4f9
Create Date: 2025-05-02 10:15:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4cfc91d5b5e9'
down_revision: Union[str, None] = '3bfc91c5b4f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create PlacementRequestStatus enum type
    placement_request_status = sa.Enum(
        'OPEN', 'IN_PROGRESS', 'REJECTED', 'ACCEPTED',
        name='placementrequeststatus'
    )
    placement_request_status.create(op.get_bind())
    
    # Create placement_requests table
    op.create_table('placement_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('status', placement_request_status, nullable=True),
        sa.Column('created_at', sa.Date(), nullable=True),
        sa.Column('email_contact_date', sa.Date(), nullable=True),
        sa.Column('phone_contact_date', sa.Date(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('response_date', sa.Date(), nullable=True),
        sa.Column('next_contact_after', sa.Date(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='matching_service'
    )
    
    # Create index on id
    op.create_index(
        op.f('ix_matching_service_placement_requests_id'), 
        'placement_requests', 
        ['id'], 
        unique=False, 
        schema='matching_service'
    )
    
    # Create indexes for foreign keys for better performance
    op.create_index(
        op.f('ix_matching_service_placement_requests_patient_id'), 
        'placement_requests', 
        ['patient_id'], 
        unique=False, 
        schema='matching_service'
    )
    
    op.create_index(
        op.f('ix_matching_service_placement_requests_therapist_id'), 
        'placement_requests', 
        ['therapist_id'], 
        unique=False, 
        schema='matching_service'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the table and indexes
    op.drop_index(
        op.f('ix_matching_service_placement_requests_therapist_id'), 
        table_name='placement_requests', 
        schema='matching_service'
    )
    op.drop_index(
        op.f('ix_matching_service_placement_requests_patient_id'), 
        table_name='placement_requests', 
        schema='matching_service'
    )
    op.drop_index(
        op.f('ix_matching_service_placement_requests_id'), 
        table_name='placement_requests', 
        schema='matching_service'
    )
    op.drop_table('placement_requests', schema='matching_service')
    
    # Drop the enum type
    sa.Enum(name='placementrequeststatus').drop(op.get_bind())