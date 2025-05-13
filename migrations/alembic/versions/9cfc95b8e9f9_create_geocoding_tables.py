"""create geocoding tables

Revision ID: 9cfc95b8e9f9
Revises: be3c0220ee8c
Create Date: 2025-05-13 13:45:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9cfc95b8e9f9'
down_revision: Union[str, None] = 'be3c0220ee8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create geocoding cache tables."""
    # Create geocache table
    op.create_table('geocache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('result_data', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        schema='geocoding_service'
    )
    
    # Create indexes for geocache
    op.create_index('ix_geocache_query', 'geocache', ['query'], 
                   schema='geocoding_service')
    op.create_index('ix_geocache_query_type', 'geocache', ['query_type'], 
                   schema='geocoding_service')
    op.create_index('ix_geocache_created_at', 'geocache', ['created_at'], 
                   schema='geocoding_service')
    
    # Create distance_cache table
    op.create_table('distance_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('origin_latitude', sa.Float(), nullable=False),
        sa.Column('origin_longitude', sa.Float(), nullable=False),
        sa.Column('destination_latitude', sa.Float(), nullable=False),
        sa.Column('destination_longitude', sa.Float(), nullable=False),
        sa.Column('travel_mode', sa.String(length=50), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('travel_time_minutes', sa.Float(), nullable=True),
        sa.Column('route_data', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        schema='geocoding_service'
    )
    
    # Create composite index for distance_cache
    op.create_index('ix_distance_cache_points', 'distance_cache', 
                   ['origin_latitude', 'origin_longitude', 
                    'destination_latitude', 'destination_longitude',
                    'travel_mode'], 
                   schema='geocoding_service')


def downgrade() -> None:
    """Drop geocoding cache tables."""
    # Drop indexes
    op.drop_index('ix_distance_cache_points', table_name='distance_cache', 
                 schema='geocoding_service')
    op.drop_index('ix_geocache_created_at', table_name='geocache', 
                 schema='geocoding_service')
    op.drop_index('ix_geocache_query_type', table_name='geocache', 
                 schema='geocoding_service')
    op.drop_index('ix_geocache_query', table_name='geocache', 
                 schema='geocoding_service')
    
    # Drop tables
    op.drop_table('distance_cache', schema='geocoding_service')
    op.drop_table('geocache', schema='geocoding_service')