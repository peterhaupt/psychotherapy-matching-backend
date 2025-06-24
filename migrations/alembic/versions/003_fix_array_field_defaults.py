"""fix patient array fields defaults

Revision ID: 003_fix_arrays
Revises: 002_remove_hardcoded_constraints
Create Date: 2025-06-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_fix_arrays'
down_revision: Union[str, None] = '002_remove_hardcoded_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix array field defaults to ensure API returns arrays, never null.
    
    This addresses the issue where bevorzugtes_therapieverfahren returns null
    instead of an empty array, causing frontend crashes.
    """
    
    print("🔧 Fixing patient array field defaults...")
    
    # Set default value for bevorzugtes_therapieverfahren to empty array
    op.execute("""
        ALTER TABLE patient_service.patienten 
        ALTER COLUMN bevorzugtes_therapieverfahren SET DEFAULT '{}'::therapieverfahren[]
    """)
    
    # Update existing NULL values to empty arrays
    op.execute("""
        UPDATE patient_service.patienten 
        SET bevorzugtes_therapieverfahren = '{}'::therapieverfahren[]
        WHERE bevorzugtes_therapieverfahren IS NULL
    """)
    
    # Also ensure ausgeschlossene_therapeuten always has default (should already be set, but let's be sure)
    op.execute("""
        UPDATE patient_service.patienten 
        SET ausgeschlossene_therapeuten = '[]'::jsonb
        WHERE ausgeschlossene_therapeuten IS NULL
    """)
    
    print("✅ Fixed bevorzugtes_therapieverfahren column:")
    print("   - Set default value to empty array for new records")
    print("   - Updated existing NULL values to empty arrays")
    print("   - Ensured ausgeschlossene_therapeuten is also never NULL")
    print("🎯 API will now always return arrays, never null")


def downgrade() -> None:
    """Revert the array field fixes.
    
    Warning: This will allow NULL values again, which can cause frontend issues.
    """
    
    print("⚠️  Reverting array field fixes...")
    
    # Remove default value for bevorzugtes_therapieverfahren
    op.execute("""
        ALTER TABLE patient_service.patienten 
        ALTER COLUMN bevorzugtes_therapieverfahren DROP DEFAULT
    """)
    
    print("❌ Removed default value for bevorzugtes_therapieverfahren")
    print("⚠️  Warning: New records may get NULL values again")
    print("🚨 This may cause frontend crashes when editing patients")