"""remove travel_time_minutes column from distance_cache

Revision ID: 006_remove_travel_time_minutes
Revises: 005_add_plz_centroids
Create Date: 2024-12-19 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_remove_travel_time_minutes'
down_revision: Union[str, None] = '005_add_plz_centroids'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove travel_time_minutes column from distance_cache table.
    
    This removes unused travel time functionality since the matching service
    only uses distance in kilometers for its constraints.
    """
    
    print("🔧 Removing travel_time_minutes column from distance_cache...")
    
    # Drop the travel_time_minutes column
    op.drop_column('distance_cache', 'travel_time_minutes', schema='geocoding_service')
    
    print("✅ Removed travel_time_minutes column from distance_cache table")
    print("🎯 Geocoding service now focuses only on distance calculations")
    print("📉 Simplified API responses and reduced database storage")


def downgrade() -> None:
    """Add back travel_time_minutes column to distance_cache table.
    
    Warning: This will restore the column but data will be lost.
    Travel time functionality would also need to be restored in the code.
    """
    
    print("⚠️  Adding back travel_time_minutes column to distance_cache...")
    
    # Add the travel_time_minutes column back
    op.add_column(
        'distance_cache',
        sa.Column('travel_time_minutes', sa.Float(), nullable=True),
        schema='geocoding_service'
    )
    
    print("🔙 Restored travel_time_minutes column")
    print("⚠️  Warning: Column is empty - previous travel time data is lost")
    print("🚨 Code changes would also need to be reverted to use travel time")