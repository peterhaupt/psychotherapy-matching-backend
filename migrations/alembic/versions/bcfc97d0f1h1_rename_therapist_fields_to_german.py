"""rename therapist fields to german

Revision ID: bcfc97d0f1h1
Revises: acfc96c9f0g0
Create Date: 2025-05-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bcfc97d0f1h1'
down_revision: Union[str, None] = 'acfc96c9f0g0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename therapist fields from English to German."""
    
    # Rename columns in therapists table
    op.alter_column('therapists', 'next_contactable_date',
                    new_column_name='naechster_kontakt_moeglich',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'preferred_diagnoses',
                    new_column_name='bevorzugte_diagnosen',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'age_min',
                    new_column_name='alter_min',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'age_max',
                    new_column_name='alter_max',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'gender_preference',
                    new_column_name='geschlechtspraeferenz',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'working_hours',
                    new_column_name='arbeitszeiten',
                    schema='therapist_service')
    
    # Also rename the index
    op.drop_index('idx_therapists_next_contactable_date', 
                  table_name='therapists', schema='therapist_service')
    op.create_index('idx_therapists_naechster_kontakt_moeglich', 'therapists', 
                    ['naechster_kontakt_moeglich'], schema='therapist_service')


def downgrade() -> None:
    """Rename therapist fields back to English."""
    
    # Drop and recreate index
    op.drop_index('idx_therapists_naechster_kontakt_moeglich', 
                  table_name='therapists', schema='therapist_service')
    op.create_index('idx_therapists_next_contactable_date', 'therapists', 
                    ['next_contactable_date'], schema='therapist_service')
    
    # Rename columns back to English
    op.alter_column('therapists', 'naechster_kontakt_moeglich',
                    new_column_name='next_contactable_date',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'bevorzugte_diagnosen',
                    new_column_name='preferred_diagnoses',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'alter_min',
                    new_column_name='age_min',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'alter_max',
                    new_column_name='age_max',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'geschlechtspraeferenz',
                    new_column_name='gender_preference',
                    schema='therapist_service')
    
    op.alter_column('therapists', 'arbeitszeiten',
                    new_column_name='working_hours',
                    schema='therapist_service')