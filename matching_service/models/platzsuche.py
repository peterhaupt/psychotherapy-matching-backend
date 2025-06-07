"""Platzsuche (Patient Search) database model - STUB."""
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, DateTime, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB

from shared.utils.database import Base


class SearchStatus(str, Enum):
    """Enumeration for patient search status values."""
    
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Platzsuche(Base):
    """Patient search tracking model.
    
    Represents an ongoing search for therapy placement for a patient.
    Tracks excluded therapists, contact attempts, and search status.
    """
    
    __tablename__ = "platzsuche"
    __table_args__ = {"schema": "matching_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Patient reference
    patient_id = Column(
        Integer,
        ForeignKey("patient_service.patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Search status
    status = Column(
        SQLAlchemyEnum(SearchStatus),
        nullable=False,
        default=SearchStatus.ACTIVE,
        index=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(DateTime)
    
    # Excluded therapists (German field name as per database)
    ausgeschlossene_therapeuten = Column(
        JSONB,
        nullable=False,
        default=list
    )
    
    # Contact tracking (German field names)
    gesamt_angeforderte_kontakte = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Success tracking (German field name)
    erfolgreiche_vermittlung_datum = Column(DateTime)
    
    # Notes (German field name)
    notizen = Column(Text)
    
    def __repr__(self):
        """String representation."""
        return f"<Platzsuche patient_id={self.patient_id} status={self.status}>"