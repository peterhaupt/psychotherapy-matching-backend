"""create therapist table

Revision ID: 3bfc91c5b4f9
Revises: 2afc91c5b3e8
Create Date: 2025-04-29 10:15:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3bfc91c5b4f9'
down_revision: Union[str, None] = '2afc91c5b3e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create TherapistStatus enum type
    therapist_status = sa.Enum('ACTIVE', 'BLOCKED', 'INACTIVE', name='therapiststatus')
    therapist_status.create(op.get_bind())
    
    # Create therapists table
    op.create_table('therapists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anrede', sa.String(length=10), nullable=True),
        sa.Column('titel', sa.String(length=20), nullable=True),
        sa.Column('vorname', sa.String(length=100), nullable=False),
        sa.Column('nachname', sa.String(length=100), nullable=False),
        sa.Column('strasse', sa.String(length=255), nullable=True),
        sa.Column('plz', sa.String(length=10), nullable=True),
        sa.Column('ort', sa.String(length=100), nullable=True),
        sa.Column('telefon', sa.String(length=50), nullable=True),
        sa.Column('fax', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('webseite', sa.String(length=255), nullable=True),
        sa.Column('kassensitz', sa.Boolean(), nullable=True),
        sa.Column('geschlecht', sa.String(length=20), nullable=True),
        sa.Column('telefonische_erreichbarkeit', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('fremdsprachen', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('psychotherapieverfahren', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('zusatzqualifikationen', sa.Text(), nullable=True),
        sa.Column('besondere_leistungsangebote', sa.Text(), nullable=True),
        sa.Column('letzter_kontakt_email', sa.Date(), nullable=True),
        sa.Column('letzter_kontakt_telefon', sa.Date(), nullable=True),
        sa.Column('letztes_persoenliches_gespraech', sa.Date(), nullable=True),
        sa.Column('freie_einzeltherapieplaetze_ab', sa.Date(), nullable=True),
        sa.Column('freie_gruppentherapieplaetze_ab', sa.Date(), nullable=True),
        sa.Column('status', therapist_status, nullable=True),
        sa.Column('sperrgrund', sa.Text(), nullable=True),
        sa.Column('sperrdatum', sa.Date(), nullable=True),
        sa.Column('created_at', sa.Date(), nullable=True),
        sa.Column('updated_at', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='therapist_service'
    )
    
    # Create index on id
    op.create_index(
        op.f('ix_therapist_service_therapists_id'), 
        'therapists', 
        ['id'], 
        unique=False, 
        schema='therapist_service'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the table and index
    op.drop_index(
        op.f('ix_therapist_service_therapists_id'), 
        table_name='therapists', 
        schema='therapist_service'
    )
    op.drop_table('therapists', schema='therapist_service')
    
    # Drop the enum type
    sa.Enum(name='therapiststatus').drop(op.get_bind())