"""Therapeutenanfrage (Therapist Inquiry/Bundle) database model - STUB."""
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, DateTime, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, String, Text
)

from shared.utils.database import Base


class ResponseType(str, Enum):
    """Enumeration for bundle response types."""
    
    FULL_ACCEPTANCE = "vollstaendige_annahme"
    PARTIAL_ACCEPTANCE = "teilweise_annahme"
    FULL_REJECTION = "vollstaendige_ablehnung"
    NO_RESPONSE = "keine_antwort"


class Therapeutenanfrage(Base):
    """Therapist inquiry (bundle) model.
    
    Represents a bundle of patients sent to a therapist.
    Tracks the response and outcome of the bundle.
    """
    
    __tablename__ = "therapeutenanfrage"
    __table_args__ = {"schema": "matching_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Therapist reference
    therapist_id = Column(
        Integer,
        ForeignKey("therapist_service.therapists.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    sent_date = Column(DateTime, index=True)
    response_date = Column(DateTime)
    
    # Response tracking (German field names)
    antworttyp = Column(
        SQLAlchemyEnum(ResponseType),
        index=True
    )
    
    # Bundle composition (German field names)
    buendelgroesse = Column(Integer, nullable=False)
    angenommen_anzahl = Column(Integer, nullable=False, default=0)
    abgelehnt_anzahl = Column(Integer, nullable=False, default=0)
    keine_antwort_anzahl = Column(Integer, nullable=False, default=0)
    
    # Notes (German field name)
    notizen = Column(Text)
    
    # Communication references
    email_id = Column(
        Integer,
        ForeignKey("communication_service.emails.id", ondelete="SET NULL"),
        index=True
    )
    phone_call_id = Column(
        Integer,
        ForeignKey("communication_service.phone_calls.id", ondelete="SET NULL"),
        index=True
    )
    
    def __repr__(self):
        """String representation."""
        return f"<Therapeutenanfrage therapist_id={self.therapist_id} size={self.buendelgroesse}>"