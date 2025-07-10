"""Phone call database models with patient support."""
from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, 
    String, Text, Time
)

from shared.utils.database import Base


class PhoneCallStatus(str, Enum):
    """Enumeration for phone call status values - fully German."""

    geplant = "geplant"
    abgeschlossen = "abgeschlossen"
    fehlgeschlagen = "fehlgeschlagen"
    abgebrochen = "abgebrochen"


class PhoneCall(Base):
    """Phone call database model with German field names and patient support.

    This model represents a scheduled or completed phone call to a therapist or patient,
    including call details, status tracking, and outcomes.
    """

    __tablename__ = "telefonanrufe"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Recipients - now supports both therapist AND patient
    # Using simple Integer instead of ForeignKey
    therapist_id = Column(Integer, nullable=True)  # References therapist_service.therapeuten.id
    patient_id = Column(Integer, nullable=True)     # References patient_service.patienten.id
    
    # NEW: Link to therapeutenanfrage (optional)
    therapeutenanfrage_id = Column(Integer, nullable=True)  # References matching_service.therapeutenanfrage.id
    
    # Scheduling - German field names
    geplantes_datum = Column(Date, nullable=False)  # scheduled_date
    geplante_zeit = Column(Time, nullable=False)  # scheduled_time
    dauer_minuten = Column(Integer, default=5)  # duration_minutes
    
    # Actual call details - German field names
    tatsaechliches_datum = Column(Date)  # actual_date
    tatsaechliche_zeit = Column(Time)  # actual_time
    
    # Status and outcome
    status = Column(String(50), default=PhoneCallStatus.geplant.value)
    ergebnis = Column(Text)  # outcome
    notizen = Column(Text)  # notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """Provide a string representation of the PhoneCall instance."""
        recipient_type = "therapist" if self.therapist_id else "patient"
        recipient_id = self.therapist_id or self.patient_id
        anfrage_info = f" anfrage={self.therapeutenanfrage_id}" if self.therapeutenanfrage_id else ""
        return (
            f"<PhoneCall id={self.id} to={recipient_type}:{recipient_id}{anfrage_info} "
            f"scheduled={self.geplantes_datum} {self.geplante_zeit} "
            f"status={self.status}>"
        )
    
    # Helper properties for patient support
    @property
    def recipient_type(self):
        """Get the type of recipient (therapist or patient)."""
        return 'therapist' if self.therapist_id else 'patient'

    @property
    def recipient_id(self):
        """Get the ID of the recipient regardless of type."""
        return self.therapist_id or self.patient_id

    def is_for_patient(self) -> bool:
        """Check if this phone call is for a patient."""
        return self.patient_id is not None

    def is_for_therapist(self) -> bool:
        """Check if this phone call is for a therapist."""
        return self.therapist_id is not None
    
    def is_for_anfrage(self) -> bool:
        """Check if this phone call is related to a therapeutenanfrage."""
        return self.therapeutenanfrage_id is not None
    
    def mark_as_completed(self, 
                         actual_date: Optional[date] = None,
                         actual_time: Optional[datetime.time] = None,
                         outcome: Optional[str] = None,
                         notes: Optional[str] = None) -> None:
        """Mark the phone call as completed.
        
        Args:
            actual_date: When the call actually happened (default: today)
            actual_time: Time of the actual call (default: scheduled time)
            outcome: The outcome of the call
            notes: Additional notes about the call
        """
        self.status = PhoneCallStatus.abgeschlossen.value
        self.tatsaechliches_datum = actual_date or date.today()
        self.tatsaechliche_zeit = actual_time or self.geplante_zeit
        if outcome:
            self.ergebnis = outcome
        if notes:
            self.notizen = notes
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, notes: Optional[str] = None) -> None:
        """Mark the phone call as failed.
        
        Args:
            notes: Reason for failure
        """
        self.status = PhoneCallStatus.fehlgeschlagen.value
        if notes:
            self.notizen = notes
        self.updated_at = datetime.utcnow()
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the phone call.
        
        Args:
            reason: Reason for cancellation
        """
        self.status = PhoneCallStatus.abgebrochen.value
        if reason:
            self.notizen = reason
        self.updated_at = datetime.utcnow()
    
    def is_overdue(self) -> bool:
        """Check if the scheduled call is overdue."""
        if self.status != PhoneCallStatus.geplant.value:
            return False
        return self.geplantes_datum < date.today()