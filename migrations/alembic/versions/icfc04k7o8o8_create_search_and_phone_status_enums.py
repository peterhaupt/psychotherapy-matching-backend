"""create search and phone status enums

Revision ID: icfc04k7o8o8
Revises: hcfc03j6n7n7
Create Date: 2025-06-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'icfc04k7o8o8'
down_revision: Union[str, None] = 'hcfc03j6n7n7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create search and phone call status enums with German values."""
    
    # Since tables are empty, just drop and recreate the columns with proper enum types
    
    # 1. Drop the existing status columns (indexes will be dropped automatically)
    op.drop_column('platzsuche', 'status', schema='matching_service')
    op.drop_column('phone_calls', 'status', schema='communication_service')
    
    # 2. Create searchstatus enum type (drop first if exists)
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS searchstatus"))
    searchstatus = sa.Enum('aktiv', 'erfolgreich', 'pausiert', 'abgebrochen', 
                          name='searchstatus')
    searchstatus.create(conn)
    
    # 3. Create phonecallstatus enum type (drop first if exists)
    conn.execute(sa.text("DROP TYPE IF EXISTS phonecallstatus"))
    phonecallstatus = sa.Enum('geplant', 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen',
                             name='phonecallstatus')
    phonecallstatus.create(conn)
    
    # 4. Add status column to platzsuche with searchstatus enum
    op.add_column('platzsuche',
                  sa.Column('status', searchstatus, nullable=False, server_default='aktiv'),
                  schema='matching_service')
    
    # 5. Add status column to phone_calls with phonecallstatus enum
    op.add_column('phone_calls',
                  sa.Column('status', phonecallstatus, nullable=False, server_default='geplant'),
                  schema='communication_service')
    
    # 6. Re-create the indexes that existed before
    op.create_index('idx_platzsuche_status', 'platzsuche', ['status'], 
                   schema='matching_service')
    op.create_index('idx_phone_calls_status', 'phone_calls', ['status'], 
                   schema='communication_service')


def downgrade() -> None:
    """Revert to string columns and drop enum types."""
    
    # 1. Drop the enum columns (indexes will be dropped automatically)
    op.drop_column('phone_calls', 'status', schema='communication_service')
    op.drop_column('platzsuche', 'status', schema='matching_service')
    
    # 2. Re-add status columns as strings
    op.add_column('platzsuche',
                  sa.Column('status', sa.String(50), nullable=False, server_default='active'),
                  schema='matching_service')
    
    op.add_column('phone_calls',
                  sa.Column('status', sa.String(50), server_default='scheduled'),
                  schema='communication_service')
    
    # 3. Re-create the indexes
    op.create_index('idx_platzsuche_status', 'platzsuche', ['status'], 
                   schema='matching_service')
    op.create_index('idx_phone_calls_status', 'phone_calls', ['status'], 
                   schema='communication_service')
    
    # 4. Drop the enum types
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS searchstatus"))
    conn.execute(sa.text("DROP TYPE IF EXISTS phonecallstatus"))