"""fix therapist jsonb field defaults

Revision ID: 004_fix_therapist_jsonb
Revises: 003_fix_arrays
Create Date: 2025-06-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_fix_therapist_jsonb'
down_revision: Union[str, None] = '003_fix_arrays'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix therapist JSONB field defaults to ensure API returns arrays/objects, never null.
    
    This addresses the issue where therapist JSONB fields return null instead of 
    empty arrays/objects, causing frontend crashes and API inconsistency.
    """
    
    print("🔧 Fixing therapist JSONB field defaults...")
    
    # ========== ARRAY FIELDS (should return empty arrays) ==========
    
    # Set default values for array-type JSONB fields
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN fremdsprachen SET DEFAULT '[]'::jsonb
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN psychotherapieverfahren SET DEFAULT '[]'::jsonb
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN bevorzugte_diagnosen SET DEFAULT '[]'::jsonb
    """)
    
    # Update existing NULL values to empty arrays for array fields
    op.execute("""
        UPDATE therapist_service.therapeuten 
        SET fremdsprachen = '[]'::jsonb
        WHERE fremdsprachen IS NULL
    """)
    
    op.execute("""
        UPDATE therapist_service.therapeuten 
        SET psychotherapieverfahren = '[]'::jsonb
        WHERE psychotherapieverfahren IS NULL
    """)
    
    op.execute("""
        UPDATE therapist_service.therapeuten 
        SET bevorzugte_diagnosen = '[]'::jsonb
        WHERE bevorzugte_diagnosen IS NULL
    """)
    
    # ========== OBJECT FIELDS (should return empty objects) ==========
    
    # Set default values for object-type JSONB fields
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN telefonische_erreichbarkeit SET DEFAULT '{}'::jsonb
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN arbeitszeiten SET DEFAULT '{}'::jsonb
    """)
    
    # Update existing NULL values to empty objects for object fields
    op.execute("""
        UPDATE therapist_service.therapeuten 
        SET telefonische_erreichbarkeit = '{}'::jsonb
        WHERE telefonische_erreichbarkeit IS NULL
    """)
    
    op.execute("""
        UPDATE therapist_service.therapeuten 
        SET arbeitszeiten = '{}'::jsonb
        WHERE arbeitszeiten IS NULL
    """)
    
    print("✅ Fixed therapist JSONB field defaults:")
    print("   Array fields (fremdsprachen, psychotherapieverfahren, bevorzugte_diagnosen):")
    print("   - Set default value to empty array for new records")
    print("   - Updated existing NULL values to empty arrays")
    print("   Object fields (telefonische_erreichbarkeit, arbeitszeiten):")
    print("   - Set default value to empty object for new records") 
    print("   - Updated existing NULL values to empty objects")
    print("🎯 API will now always return arrays/objects, never null")


def downgrade() -> None:
    """Revert the JSONB field fixes.
    
    Warning: This will allow NULL values again, which can cause frontend issues.
    """
    
    print("⚠️  Reverting therapist JSONB field fixes...")
    
    # Remove default values for all JSONB fields
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN fremdsprachen DROP DEFAULT
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN psychotherapieverfahren DROP DEFAULT
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN bevorzugte_diagnosen DROP DEFAULT
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN telefonische_erreichbarkeit DROP DEFAULT
    """)
    
    op.execute("""
        ALTER TABLE therapist_service.therapeuten 
        ALTER COLUMN arbeitszeiten DROP DEFAULT
    """)
    
    print("❌ Removed default values for therapist JSONB fields")
    print("⚠️  Warning: New records may get NULL values again")
    print("🚨 This may cause frontend crashes when editing therapists")