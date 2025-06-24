"""remove hardcoded anfrage size constraints

Revision ID: 002_remove_hardcoded_constraints
Revises: 001_initial_setup
Create Date: 2025-01-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_remove_hardcoded_constraints'
down_revision: Union[str, None] = '001_initial_setup'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove the hardcoded check constraint for anfragegroesse.
    
    This allows the application to use dynamic configuration values
    from environment variables instead of database-level constraints.
    """
    
    # Drop the existing hardcoded check constraint for anfrage size
    op.drop_constraint(
        'anfrage_size_check',
        'therapeutenanfrage',
        schema='matching_service',
        type_='check'
    )
    
    print("✅ Removed hardcoded anfrage size constraint (was: anfragegroesse >= 3 AND anfragegroesse <= 6)")
    print("🔧 Application will now use MIN_ANFRAGE_SIZE and MAX_ANFRAGE_SIZE environment variables")
    
    # Note: We keep the other check constraints as they are still valid:
    # - accepted_count_check: angenommen_anzahl >= 0
    # - rejected_count_check: abgelehnt_anzahl >= 0  
    # - no_response_count_check: keine_antwort_anzahl >= 0
    # These are not hardcoded business rules but basic data integrity constraints


def downgrade() -> None:
    """Re-add the hardcoded check constraint.
    
    Note: This restores the old behavior with hardcoded values (min=3, max=6).
    Only use this if you need to revert to the previous system.
    """
    
    # Re-add the hardcoded anfrage size constraint with old values
    op.create_check_constraint(
        'anfrage_size_check',
        'therapeutenanfrage',
        'anfragegroesse >= 3 AND anfragegroesse <= 6',
        schema='matching_service'
    )
    
    print("⚠️  Restored hardcoded anfrage size constraint (anfragegroesse >= 3 AND anfragegroesse <= 6)")
    print("🔙 Application will ignore MIN_ANFRAGE_SIZE and MAX_ANFRAGE_SIZE environment variables")