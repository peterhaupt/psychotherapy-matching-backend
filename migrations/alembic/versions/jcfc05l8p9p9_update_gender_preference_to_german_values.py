"""update gender preference enum to german values

Revision ID: jcfc05l8p9p9
Revises: icfc04k7o8o8
Create Date: 2025-06-11 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'jcfc05l8p9p9'
down_revision: Union[str, None] = 'icfc04k7o8o8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update therapistgenderpreference enum to use German values."""
    
    # First, we need to update any existing data that uses the old enum values
    # We'll temporarily convert the column to text to do the mapping
    
    # Step 1: Alter the column to text type temporarily
    op.execute("""
        ALTER TABLE patient_service.patients 
        ALTER COLUMN bevorzugtes_therapeutengeschlecht 
        TYPE VARCHAR(50) 
        USING bevorzugtes_therapeutengeschlecht::text
    """)
    
    # Step 2: Update existing values from English to German
    op.execute("""
        UPDATE patient_service.patients 
        SET bevorzugtes_therapeutengeschlecht = CASE bevorzugtes_therapeutengeschlecht
            WHEN 'MALE' THEN 'Männlich'
            WHEN 'FEMALE' THEN 'Weiblich'
            WHEN 'ANY' THEN 'Egal'
            ELSE bevorzugtes_therapeutengeschlecht
        END
        WHERE bevorzugtes_therapeutengeschlecht IN ('MALE', 'FEMALE', 'ANY')
    """)
    
    # Step 3: Rename the old enum type
    op.execute("ALTER TYPE therapistgenderpreference RENAME TO therapistgenderpreference_old")
    
    # Step 4: Create new enum type with German values
    therapistgenderpreference = sa.Enum('Männlich', 'Weiblich', 'Egal', 
                                      name='therapistgenderpreference')
    therapistgenderpreference.create(op.get_bind())
    
    # Step 5: Alter the column to use the new enum type
    op.execute("""
        ALTER TABLE patient_service.patients 
        ALTER COLUMN bevorzugtes_therapeutengeschlecht 
        TYPE therapistgenderpreference 
        USING bevorzugtes_therapeutengeschlecht::therapistgenderpreference
    """)
    
    # Step 6: Drop the old enum type
    op.execute("DROP TYPE therapistgenderpreference_old")


def downgrade() -> None:
    """Revert therapistgenderpreference enum back to English values."""
    
    # Step 1: Alter the column to text type temporarily
    op.execute("""
        ALTER TABLE patient_service.patients 
        ALTER COLUMN bevorzugtes_therapeutengeschlecht 
        TYPE VARCHAR(50) 
        USING bevorzugtes_therapeutengeschlecht::text
    """)
    
    # Step 2: Update existing values from German to English
    op.execute("""
        UPDATE patient_service.patients 
        SET bevorzugtes_therapeutengeschlecht = CASE bevorzugtes_therapeutengeschlecht
            WHEN 'Männlich' THEN 'MALE'
            WHEN 'Weiblich' THEN 'FEMALE'
            WHEN 'Egal' THEN 'ANY'
            ELSE bevorzugtes_therapeutengeschlecht
        END
        WHERE bevorzugtes_therapeutengeschlecht IN ('Männlich', 'Weiblich', 'Egal')
    """)
    
    # Step 3: Rename the current enum type
    op.execute("ALTER TYPE therapistgenderpreference RENAME TO therapistgenderpreference_old")
    
    # Step 4: Create old enum type with English values
    therapistgenderpreference = sa.Enum('MALE', 'FEMALE', 'ANY', 
                                      name='therapistgenderpreference')
    therapistgenderpreference.create(op.get_bind())
    
    # Step 5: Alter the column to use the old enum type
    op.execute("""
        ALTER TABLE patient_service.patients 
        ALTER COLUMN bevorzugtes_therapeutengeschlecht 
        TYPE therapistgenderpreference 
        USING bevorzugtes_therapeutengeschlecht::therapistgenderpreference
    """)
    
    # Step 6: Drop the temporary enum type
    op.execute("DROP TYPE therapistgenderpreference_old")