"""remove placement requests use bundle system

Revision ID: fcfc01h4l5l5
Revises: ecfc00g3k4k4
Create Date: 2025-05-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fcfc01h4l5l5'
down_revision: Union[str, None] = 'ecfc00g3k4k4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove placement_requests and update foreign keys to use bundle system."""
    
    # 1. Drop foreign key constraints that reference placement_requests
    op.drop_constraint('email_batches_placement_request_id_fkey', 'email_batches', 
                      schema='communication_service', type_='foreignkey')
    op.drop_constraint('phone_call_batches_placement_request_id_fkey', 'phone_call_batches',
                      schema='communication_service', type_='foreignkey')
    
    # 2. Add new column for therapeut_anfrage_patient reference
    op.add_column('email_batches',
                  sa.Column('therapeut_anfrage_patient_id', sa.Integer(), nullable=True),
                  schema='communication_service')
    
    op.add_column('phone_call_batches',
                  sa.Column('therapeut_anfrage_patient_id', sa.Integer(), nullable=True),
                  schema='communication_service')
    
    # 3. Create new foreign key constraints
    op.create_foreign_key('email_batches_therapeut_anfrage_patient_id_fkey',
                         'email_batches', 'therapeut_anfrage_patient',
                         ['therapeut_anfrage_patient_id'], ['id'],
                         source_schema='communication_service',
                         referent_schema='matching_service',
                         ondelete='CASCADE')
    
    op.create_foreign_key('phone_call_batches_therapeut_anfrage_patient_id_fkey',
                         'phone_call_batches', 'therapeut_anfrage_patient',
                         ['therapeut_anfrage_patient_id'], ['id'],
                         source_schema='communication_service',
                         referent_schema='matching_service',
                         ondelete='CASCADE')
    
    # 4. Drop old placement_request_id columns
    op.drop_column('email_batches', 'placement_request_id', schema='communication_service')
    op.drop_column('phone_call_batches', 'placement_request_id', schema='communication_service')
    
    # 5. Update indexes
    op.create_index('idx_email_batches_therapeut_anfrage_patient_id', 'email_batches',
                   ['therapeut_anfrage_patient_id'], schema='communication_service')
    op.create_index('idx_phone_call_batches_therapeut_anfrage_patient_id', 'phone_call_batches',
                   ['therapeut_anfrage_patient_id'], schema='communication_service')
    
    # 6. Drop all indexes on placement_requests table
    op.drop_index('ix_matching_service_placement_requests_therapist_id', 
                 table_name='placement_requests', schema='matching_service')
    op.drop_index('ix_matching_service_placement_requests_patient_id', 
                 table_name='placement_requests', schema='matching_service')
    op.drop_index('ix_matching_service_placement_requests_id', 
                 table_name='placement_requests', schema='matching_service')
    
    # 7. Drop the placement_requests table
    op.drop_table('placement_requests', schema='matching_service')
    
    # 8. Drop the PlacementRequestStatus enum type
    op.execute("DROP TYPE IF EXISTS placementrequeststatus")


def downgrade() -> None:
    """Recreate placement_requests and restore original foreign keys."""
    
    # 1. Recreate the PlacementRequestStatus enum
    placementrequeststatus = sa.Enum('OPEN', 'IN_PROGRESS', 'REJECTED', 'ACCEPTED', 
                                    name='placementrequeststatus')
    placementrequeststatus.create(op.get_bind())
    
    # 2. Recreate placement_requests table
    op.create_table('placement_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('status', placementrequeststatus, nullable=True),
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
    
    # 3. Recreate indexes
    op.create_index('ix_matching_service_placement_requests_id', 'placement_requests', 
                   ['id'], unique=False, schema='matching_service')
    op.create_index('ix_matching_service_placement_requests_patient_id', 'placement_requests', 
                   ['patient_id'], unique=False, schema='matching_service')
    op.create_index('ix_matching_service_placement_requests_therapist_id', 'placement_requests', 
                   ['therapist_id'], unique=False, schema='matching_service')
    
    # 4. Drop new indexes
    op.drop_index('idx_phone_call_batches_therapeut_anfrage_patient_id', 
                 table_name='phone_call_batches', schema='communication_service')
    op.drop_index('idx_email_batches_therapeut_anfrage_patient_id', 
                 table_name='email_batches', schema='communication_service')
    
    # 5. Add back placement_request_id columns
    op.add_column('phone_call_batches',
                  sa.Column('placement_request_id', sa.Integer(), nullable=False),
                  schema='communication_service')
    
    op.add_column('email_batches',
                  sa.Column('placement_request_id', sa.Integer(), nullable=False),
                  schema='communication_service')
    
    # 6. Drop new foreign key constraints
    op.drop_constraint('phone_call_batches_therapeut_anfrage_patient_id_fkey',
                      'phone_call_batches', schema='communication_service', type_='foreignkey')
    op.drop_constraint('email_batches_therapeut_anfrage_patient_id_fkey',
                      'email_batches', schema='communication_service', type_='foreignkey')
    
    # 7. Drop new columns
    op.drop_column('phone_call_batches', 'therapeut_anfrage_patient_id', 
                  schema='communication_service')
    op.drop_column('email_batches', 'therapeut_anfrage_patient_id', 
                  schema='communication_service')
    
    # 8. Recreate original foreign key constraints
    op.create_foreign_key('phone_call_batches_placement_request_id_fkey',
                         'phone_call_batches', 'placement_requests',
                         ['placement_request_id'], ['id'],
                         source_schema='communication_service',
                         referent_schema='matching_service',
                         ondelete='CASCADE')
    
    op.create_foreign_key('email_batches_placement_request_id_fkey',
                         'email_batches', 'placement_requests',
                         ['placement_request_id'], ['id'],
                         source_schema='communication_service',
                         referent_schema='matching_service',
                         ondelete='CASCADE')