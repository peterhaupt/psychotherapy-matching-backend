"""add bundle system tables

Revision ID: acfc96c9f0g0
Revises: 9cfc95b8e9f9
Create Date: 2025-05-20 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'acfc96c9f0g0'
down_revision: Union[str, None] = '9cfc95b8e9f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bundle system tables and missing therapist columns."""
    
    # 1. Add missing columns to therapists table
    op.add_column('therapists', 
                  sa.Column('next_contactable_date', sa.Date(), nullable=True),
                  schema='therapist_service')
    
    op.add_column('therapists', 
                  sa.Column('preferred_diagnoses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                  schema='therapist_service')
    
    op.add_column('therapists', 
                  sa.Column('age_min', sa.Integer(), nullable=True),
                  schema='therapist_service')
    
    op.add_column('therapists', 
                  sa.Column('age_max', sa.Integer(), nullable=True),
                  schema='therapist_service')
    
    op.add_column('therapists', 
                  sa.Column('gender_preference', sa.String(50), nullable=True),
                  schema='therapist_service')
    
    op.add_column('therapists', 
                  sa.Column('working_hours', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                  schema='therapist_service')
    
    # 2. Create platzsuche (patient search) table
    op.create_table('platzsuche',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('excluded_therapists', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default='[]'),
        sa.Column('total_requested_contacts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_match_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patient_service.patients.id'], 
                               ondelete='CASCADE'),
        schema='matching_service'
    )
    
    # Create indexes for platzsuche
    op.create_index('idx_platzsuche_patient_id', 'platzsuche', ['patient_id'], 
                   schema='matching_service')
    op.create_index('idx_platzsuche_status', 'platzsuche', ['status'], 
                   schema='matching_service')
    
    # 3. Create therapeutenanfrage (therapist inquiry/bundle) table
    op.create_table('therapeutenanfrage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('created_date', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sent_date', sa.DateTime(), nullable=True),
        sa.Column('response_date', sa.DateTime(), nullable=True),
        sa.Column('response_type', sa.String(50), nullable=True),
        sa.Column('bundle_size', sa.Integer(), nullable=False),
        sa.Column('accepted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejected_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('no_response_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['therapist_id'], ['therapist_service.therapists.id'], 
                               ondelete='CASCADE'),
        schema='matching_service'
    )
    
    # Create indexes for therapeutenanfrage
    op.create_index('idx_therapeutenanfrage_therapist_id', 'therapeutenanfrage', 
                   ['therapist_id'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_sent_date', 'therapeutenanfrage', 
                   ['sent_date'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_response_type', 'therapeutenanfrage', 
                   ['response_type'], schema='matching_service')
    
    # 4. Create therapeut_anfrage_patient (bundle composition) table
    op.create_table('therapeut_anfrage_patient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapeutenanfrage_id', sa.Integer(), nullable=False),
        sa.Column('platzsuche_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('position_in_bundle', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('response_outcome', sa.String(50), nullable=True),
        sa.Column('response_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['therapeutenanfrage_id'], 
                               ['matching_service.therapeutenanfrage.id'], 
                               ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platzsuche_id'], 
                               ['matching_service.platzsuche.id'], 
                               ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], 
                               ['patient_service.patients.id'], 
                               ondelete='CASCADE'),
        sa.UniqueConstraint('therapeutenanfrage_id', 'platzsuche_id', 
                          name='uq_therapeut_anfrage_patient_bundle_search'),
        schema='matching_service'
    )
    
    # Create indexes for therapeut_anfrage_patient
    op.create_index('idx_therapeut_anfrage_patient_therapeutenanfrage_id', 
                   'therapeut_anfrage_patient', ['therapeutenanfrage_id'], 
                   schema='matching_service')
    op.create_index('idx_therapeut_anfrage_patient_platzsuche_id', 
                   'therapeut_anfrage_patient', ['platzsuche_id'], 
                   schema='matching_service')
    op.create_index('idx_therapeut_anfrage_patient_patient_id', 
                   'therapeut_anfrage_patient', ['patient_id'], 
                   schema='matching_service')
    op.create_index('idx_therapeut_anfrage_patient_status', 
                   'therapeut_anfrage_patient', ['status'], 
                   schema='matching_service')
    
    # 5. Create an index on therapists.next_contactable_date for efficient cooling period queries
    op.create_index('idx_therapists_next_contactable_date', 'therapists', 
                   ['next_contactable_date'], schema='therapist_service')


def downgrade() -> None:
    """Remove bundle system tables and added columns."""
    
    # 1. Drop indexes
    op.drop_index('idx_therapists_next_contactable_date', table_name='therapists', 
                 schema='therapist_service')
    
    op.drop_index('idx_therapeut_anfrage_patient_status', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_index('idx_therapeut_anfrage_patient_patient_id', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_index('idx_therapeut_anfrage_patient_platzsuche_id', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_index('idx_therapeut_anfrage_patient_therapeutenanfrage_id', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    
    op.drop_index('idx_therapeutenanfrage_response_type', 
                 table_name='therapeutenanfrage', schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_sent_date', 
                 table_name='therapeutenanfrage', schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_therapist_id', 
                 table_name='therapeutenanfrage', schema='matching_service')
    
    op.drop_index('idx_platzsuche_status', table_name='platzsuche', schema='matching_service')
    op.drop_index('idx_platzsuche_patient_id', table_name='platzsuche', schema='matching_service')
    
    # 2. Drop tables
    op.drop_table('therapeut_anfrage_patient', schema='matching_service')
    op.drop_table('therapeutenanfrage', schema='matching_service')
    op.drop_table('platzsuche', schema='matching_service')
    
    # 3. Drop columns from therapists
    op.drop_column('therapists', 'working_hours', schema='therapist_service')
    op.drop_column('therapists', 'gender_preference', schema='therapist_service')
    op.drop_column('therapists', 'age_max', schema='therapist_service')
    op.drop_column('therapists', 'age_min', schema='therapist_service')
    op.drop_column('therapists', 'preferred_diagnoses', schema='therapist_service')
    op.drop_column('therapists', 'next_contactable_date', schema='therapist_service')