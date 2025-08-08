"""Phase 2 patient table updates - Remove diagnosis/PTV11, convert symptome to JSONB, add payment fields

Revision ID: 003_phase2_patient_updates
Revises: 002_therapeutenanfrage_id
Create Date: 2025-01-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '003_phase2_patient_updates'
down_revision = '002_therapeutenanfrage_id'
branch_labels = None
depends_on = None


def upgrade():
    """Apply Phase 2 patient table updates."""
    
    print("Starting Phase 2 patient table updates...")
    
    # 1. Remove diagnose field completely (data will be lost)
    print("Removing diagnose field...")
    op.drop_column('patienten', 'diagnose', schema='patient_service')
    
    # 2. Remove psychotherapeutische_sprechstunde field (PTV11 related)
    print("Removing psychotherapeutische_sprechstunde field...")
    op.drop_column('patienten', 'psychotherapeutische_sprechstunde', schema='patient_service')
    
    # 3. Change symptome from TEXT to JSONB
    # First, we need to drop the existing column and recreate it as JSONB
    # All existing data will be lost as per the implementation plan
    print("Converting symptome field to JSONB (existing data will be cleared)...")
    
    # Drop the old TEXT column
    op.drop_column('patienten', 'symptome', schema='patient_service')
    
    # Add new JSONB column (nullable, will be NULL for all existing records)
    op.add_column(
        'patienten',
        sa.Column('symptome', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema='patient_service'
    )
    
    # 4. Add zahlungsreferenz field (nullable for existing patients)
    print("Adding zahlungsreferenz field...")
    op.add_column(
        'patienten',
        sa.Column('zahlungsreferenz', sa.String(8), nullable=True),
        schema='patient_service'
    )
    
    # 5. Add zahlung_eingegangen field with default FALSE
    print("Adding zahlung_eingegangen field...")
    op.add_column(
        'patienten',
        sa.Column('zahlung_eingegangen', sa.Boolean(), nullable=False, server_default='false'),
        schema='patient_service'
    )
    
    print("Phase 2 patient table updates completed successfully!")
    print("NOTE: All existing symptome data has been cleared. Manual re-entry required through admin interface.")


def downgrade():
    """Revert Phase 2 patient table updates."""
    
    print("Reverting Phase 2 patient table updates...")
    
    # Remove the payment fields
    op.drop_column('patienten', 'zahlung_eingegangen', schema='patient_service')
    op.drop_column('patienten', 'zahlungsreferenz', schema='patient_service')
    
    # Revert symptome back to TEXT (data will be lost)
    op.drop_column('patienten', 'symptome', schema='patient_service')
    op.add_column(
        'patienten',
        sa.Column('symptome', sa.Text(), nullable=True),
        schema='patient_service'
    )
    
    # Re-add the removed fields
    op.add_column(
        'patienten',
        sa.Column('psychotherapeutische_sprechstunde', sa.Boolean(), nullable=True, server_default='false'),
        schema='patient_service'
    )
    
    op.add_column(
        'patienten',
        sa.Column('diagnose', sa.String(50), nullable=True),
        schema='patient_service'
    )
    
    print("Phase 2 patient table updates reverted.")
    print("WARNING: Data loss has occurred during this migration cycle.")