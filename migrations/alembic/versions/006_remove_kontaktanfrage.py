"""Remove legacy kontaktanfrage field from platzsuche table

Revision ID: 006_remove_kontaktanfrage
Revises: 005_vermittelter_therapeut
Create Date: 2025-01-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_remove_kontaktanfrage'
down_revision = '005_vermittelter_therapeut'
branch_labels = None
depends_on = None


def upgrade():
    """Remove gesamt_angeforderte_kontakte column from platzsuche table."""
    print("Removing gesamt_angeforderte_kontakte from platzsuche table...")
    
    # Drop the column
    op.drop_column(
        'platzsuche',
        'gesamt_angeforderte_kontakte',
        schema='matching_service'
    )
    
    print("Successfully removed gesamt_angeforderte_kontakte column")


def downgrade():
    """Re-add gesamt_angeforderte_kontakte column to platzsuche table."""
    print("Re-adding gesamt_angeforderte_kontakte to platzsuche table...")
    
    # Re-add the column
    op.add_column(
        'platzsuche',
        sa.Column('gesamt_angeforderte_kontakte', sa.Integer(), nullable=False, server_default='0'),
        schema='matching_service'
    )
    
    print("Successfully re-added gesamt_angeforderte_kontakte column")