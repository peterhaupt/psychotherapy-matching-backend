"""TherapeutAnfragePatient (Bundle Composition) database model - STUB."""
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, DateTime, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, String, Text, UniqueConstraint
)

from shared.utils.database import Base


class PatientStatus(str, Enum):
    """Enumeration for patient status within a bundle."""
    
    PENDING = "pending"
    ACCEPTED = "angenommen"
    REJECTED = "abgelehnt"
    NO_RESPONSE = "keine_antwort"


class PatientOutcome(str, Enum):
    """Enumeration for patient response outcomes."""
    
    ACCEPTED = "angenommen"
    REJECTED_CAPACITY = "abgelehnt_kapazitaet"
    REJECTED_NOT_SUITABLE = "abgelehnt_nicht_geeignet"
    REJECTED_OTHER = "abgelehnt_sonstiges"
    NO_SHOW = "nicht_erschienen"
    IN_SESSIONS = "in_sitzungen"


class TherapeutAnfragePatient(Base):
    """Bundle composition model.
    
    Links patients to therapist inquiries (bundles) and tracks
    individual patient outcomes within the bundle.
    """
    
    __tablename__ = "therapeut_anfrage_patient"
    __table_args__ = (
        UniqueConstraint(
            'therapeutenanfrage_id', 
            'platzsuche_id',
            name='uq_therapeut_anfrage_patient_bundle_search'
        ),
        {"schema": "matching_service"}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Bundle reference
    therapeutenanfrage_id = Column(
        Integer,
        ForeignKey("matching_service.therapeutenanfrage.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Search reference
    platzsuche_id = Column(
        Integer,
        ForeignKey("matching_service.platzsuche.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Patient reference
    patient_id = Column(
        Integer,
        ForeignKey("patient_service.patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Position tracking (German field name)
    position_im_buendel = Column(Integer, nullable=False)
    
    # Status tracking
    status = Column(
        SQLAlchemyEnum(PatientStatus),
        nullable=False,
        default=PatientStatus.PENDING,
        index=True
    )
    
    # Outcome tracking (German field names)
    antwortergebnis = Column(SQLAlchemyEnum(PatientOutcome))
    antwortnotizen = Column(Text)
    
    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    def __repr__(self):
        """String representation."""
        return (
            f"<TherapeutAnfragePatient "
            f"bundle={self.therapeutenanfrage_id} "
            f"patient={self.patient_id} "
            f"status={self.status}>"
        )