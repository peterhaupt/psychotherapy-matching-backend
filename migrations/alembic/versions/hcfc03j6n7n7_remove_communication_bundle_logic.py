"""remove communication bundle logic

Revision ID: hcfc03j6n7n7
Revises: gcfc02i5m6m6
Create Date: 2025-05-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'hcfc03j6n7n7'
down_revision: Union[str, None] = 'gcfc02i5m6m6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove bundle logic from communication service and move references to matching service."""
    
    # 1. Drop indexes on the batch tables first
    op.drop_index('idx_email_batches_therapeut_anfrage_patient_id', 
                  table_name='email_batches', schema='communication_service')
    op.drop_index('idx_email_batches_email_id', 
                  table_name='email_batches', schema='communication_service')
    
    op.drop_index('idx_phone_call_batches_therapeut_anfrage_patient_id', 
                  table_name='phone_call_batches', schema='communication_service')
    op.drop_index('idx_phone_call_batches_phone_call_id', 
                  table_name='phone_call_batches', schema='communication_service')
    
    # 2. Drop the batch tables
    op.drop_table('email_batches', schema='communication_service')
    op.drop_table('phone_call_batches', schema='communication_service')
    
    # 3. Add communication references to therapeutenanfrage table
    op.add_column('therapeutenanfrage',
                  sa.Column('email_id', sa.Integer(), nullable=True),
                  schema='matching_service')
    
    op.add_column('therapeutenanfrage',
                  sa.Column('phone_call_id', sa.Integer(), nullable=True),
                  schema='matching_service')
    
    # 4. Create foreign key constraints
    op.create_foreign_key('therapeutenanfrage_email_id_fkey',
                          'therapeutenanfrage', 'emails',
                          ['email_id'], ['id'],
                          source_schema='matching_service',
                          referent_schema='communication_service',
                          ondelete='SET NULL')
    
    op.create_foreign_key('therapeutenanfrage_phone_call_id_fkey',
                          'therapeutenanfrage', 'phone_calls',
                          ['phone_call_id'], ['id'],
                          source_schema='matching_service',
                          referent_schema='communication_service',
                          ondelete='SET NULL')
    
    # 5. Create indexes for the new foreign keys
    op.create_index('idx_therapeutenanfrage_email_id', 'therapeutenanfrage',
                    ['email_id'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_phone_call_id', 'therapeutenanfrage',
                    ['phone_call_id'], schema='matching_service')
    
    # 6. Remove the legacy placement_request_ids column from emails
    op.drop_column('emails', 'placement_request_ids', schema='communication_service')
    
    # 7. Remove batch_id column from emails (no longer needed)
    op.drop_column('emails', 'batch_id', schema='communication_service')


def downgrade() -> None:
    """Restore bundle logic to communication service."""
    
    # 1. Restore batch_id column to emails
    op.add_column('emails',
                  sa.Column('batch_id', sa.String(50), nullable=True),
                  schema='communication_service')
    
    # 2. Restore placement_request_ids column to emails
    op.add_column('emails',
                  sa.Column('placement_request_ids', postgresql.JSONB(), nullable=True),
                  schema='communication_service')
    
    # 3. Drop indexes on therapeutenanfrage
    op.drop_index('idx_therapeutenanfrage_phone_call_id', 
                  table_name='therapeutenanfrage', schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_email_id', 
                  table_name='therapeutenanfrage', schema='matching_service')
    
    # 4. Drop foreign key constraints
    op.drop_constraint('therapeutenanfrage_phone_call_id_fkey',
                       'therapeutenanfrage', schema='matching_service', type_='foreignkey')
    op.drop_constraint('therapeutenanfrage_email_id_fkey',
                       'therapeutenanfrage', schema='matching_service', type_='foreignkey')
    
    # 5. Drop columns from therapeutenanfrage
    op.drop_column('therapeutenanfrage', 'phone_call_id', schema='matching_service')
    op.drop_column('therapeutenanfrage', 'email_id', schema='matching_service')
    
    # 6. Recreate email_batches table
    op.create_table('email_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('therapeut_anfrage_patient_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=True),
        sa.Column('included', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('antwortergebnis', sa.String(50), nullable=True),
        sa.Column('antwortnotizen', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), 
                 server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['communication_service.emails.id'], 
                              ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['therapeut_anfrage_patient_id'], 
                              ['matching_service.therapeut_anfrage_patient.id'], 
                              ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='communication_service'
    )
    
    # 7. Recreate phone_call_batches table
    op.create_table('phone_call_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_call_id', sa.Integer(), nullable=False),
        sa.Column('therapeut_anfrage_patient_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=True),
        sa.Column('discussed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('ergebnis', sa.String(50), nullable=True),
        sa.Column('nachverfolgung_erforderlich', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('nachverfolgung_notizen', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), 
                 server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['phone_call_id'], 
                              ['communication_service.phone_calls.id'], 
                              ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['therapeut_anfrage_patient_id'], 
                              ['matching_service.therapeut_anfrage_patient.id'], 
                              ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='communication_service'
    )
    
    # 8. Recreate indexes for batch tables
    op.create_index('idx_email_batches_email_id', 'email_batches',
                    ['email_id'], schema='communication_service')
    op.create_index('idx_email_batches_therapeut_anfrage_patient_id', 'email_batches',
                    ['therapeut_anfrage_patient_id'], schema='communication_service')
    
    op.create_index('idx_phone_call_batches_phone_call_id', 'phone_call_batches',
                    ['phone_call_id'], schema='communication_service')
    op.create_index('idx_phone_call_batches_therapeut_anfrage_patient_id', 'phone_call_batches',
                    ['therapeut_anfrage_patient_id'], schema='communication_service')