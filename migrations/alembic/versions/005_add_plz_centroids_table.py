"""add plz centroids table for fast distance calculation

Revision ID: 005_add_plz_centroids
Revises: 004_fix_therapist_jsonb
Create Date: 2025-01-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_plz_centroids'
down_revision: Union[str, None] = '004_fix_therapist_jsonb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add PLZ centroids table for fast distance approximation.
    
    This table stores German postal code (PLZ) centroids with their geographic
    coordinates to enable fast distance calculations without external API calls.
    """
    
    print("🔧 Creating PLZ centroids table for fast distance calculation...")
    
    # Create the PLZ centroids table
    op.create_table(
        'plz_centroids',
        sa.Column('plz', sa.String(5), primary_key=True),
        sa.Column('ort', sa.String(255), nullable=False),
        sa.Column('bundesland', sa.String(100)),
        sa.Column('bundesland_code', sa.String(2)),
        sa.Column('latitude', sa.Float, nullable=False),
        sa.Column('longitude', sa.Float, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
        schema='geocoding_service'
    )
    
    # Create index for fast lookups
    op.create_index(
        'idx_plz_centroids_plz', 
        'plz_centroids', 
        ['plz'], 
        schema='geocoding_service'
    )
    
    # Add table comment
    op.execute("""
        COMMENT ON TABLE geocoding_service.plz_centroids IS 
        'German postal code centroids for fast distance approximation'
    """)
    
    print("✅ Created PLZ centroids table:")
    print("   - Table: geocoding_service.plz_centroids")
    print("   - Primary key: plz (5-character postal code)")
    print("   - Indexed for fast lookups")
    print("   - Ready for data import (~8,200 German postal codes)")
    print("")
    print("📝 Next steps:")
    print("   1. Download PLZ data from https://github.com/zauberware/postal-codes-json-xml-csv")
    print("   2. Run the import script: python geocoding_service/scripts/import_plz_centroids.py de.json")
    print("   3. Update geocoding service to use PLZ-based distance calculation")


def downgrade() -> None:
    """Remove the PLZ centroids table.
    
    Warning: This will delete all imported PLZ data and disable fast distance calculation.
    """
    
    print("⚠️  Removing PLZ centroids table...")
    
    # Drop the index first
    op.drop_index(
        'idx_plz_centroids_plz', 
        table_name='plz_centroids',
        schema='geocoding_service'
    )
    
    # Drop the table
    op.drop_table('plz_centroids', schema='geocoding_service')
    
    print("❌ Removed PLZ centroids table")
    print("⚠️  Warning: Fast PLZ-based distance calculation is now disabled")
    print("🚨 The system will fall back to external geocoding API calls")