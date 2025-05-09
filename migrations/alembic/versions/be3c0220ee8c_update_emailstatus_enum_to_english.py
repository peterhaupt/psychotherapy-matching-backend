"""update_emailstatus_enum_to_english

Revision ID: be3c0220ee8c
Revises: 8bfc94a7d8f9
Create Date: 2025-05-09 11:59:13.215811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'be3c0220ee8c'  # Use your actual auto-generated ID 
down_revision: Union[str, None] = '8bfc94a7d8f9'  # Your latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade the emailstatus enum to use English values."""
    # Create a temporary copy of the old enum type with English values
    op.execute("ALTER TYPE emailstatus RENAME TO emailstatus_old")
    op.execute("CREATE TYPE emailstatus AS ENUM ('DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED')")
    
    # Create a mapping between old and new enum values
    mapping = """
    CASE status::text
        WHEN 'entwurf' THEN 'DRAFT'::emailstatus
        WHEN 'in_warteschlange' THEN 'QUEUED'::emailstatus
        WHEN 'wird_gesendet' THEN 'SENDING'::emailstatus
        WHEN 'gesendet' THEN 'SENT'::emailstatus
        WHEN 'fehlgeschlagen' THEN 'FAILED'::emailstatus
        ELSE 'DRAFT'::emailstatus
    END
    """
    
    # Update all tables using the emailstatus enum
    op.execute(f"ALTER TABLE communication_service.emails ALTER COLUMN status TYPE emailstatus USING {mapping}")
    
    # Drop the old enum type
    op.execute("DROP TYPE emailstatus_old")


def downgrade() -> None:
    """Revert the emailstatus enum back to German values."""
    # Create a temporary copy of the old enum type with German values
    op.execute("ALTER TYPE emailstatus RENAME TO emailstatus_old")
    op.execute("CREATE TYPE emailstatus AS ENUM ('entwurf', 'in_warteschlange', 'wird_gesendet', 'gesendet', 'fehlgeschlagen')")
    
    # Create a mapping between old and new enum values
    mapping = """
    CASE status::text
        WHEN 'DRAFT' THEN 'entwurf'::emailstatus
        WHEN 'QUEUED' THEN 'in_warteschlange'::emailstatus
        WHEN 'SENDING' THEN 'wird_gesendet'::emailstatus
        WHEN 'SENT' THEN 'gesendet'::emailstatus
        WHEN 'FAILED' THEN 'fehlgeschlagen'::emailstatus
        ELSE 'entwurf'::emailstatus
    END
    """
    
    # Update all tables using the emailstatus enum
    op.execute(f"ALTER TABLE communication_service.emails ALTER COLUMN status TYPE emailstatus USING {mapping}")
    
    # Drop the old enum type
    op.execute("DROP TYPE emailstatus_old")