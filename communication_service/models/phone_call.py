"""Phone call database models."""
from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, 
    String, Text, Time
)
from sqlalchemy.orm import relationship

from shared.utils.database import Base


class PhoneCallStatus(str, Enum):
    """Enumeration for phone call status values."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PhoneCall(Base):
    """Phone call database model with German field names.

    This model represents a scheduled or completed phone call to a therapist,
    including call details, status tracking, and outcomes.
    """

    __tablename__ = "phone_calls"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, nullable=False)
    
    # Scheduling - German field names
    geplantes_datum = Column(Date, nullable=False)  # scheduled_date
    geplante_zeit = Column(Time, nullable=False)  # scheduled_time
    dauer_minuten = Column(Integer, default=5)  # duration_minutes
    
    # Actual call details - German field names
    tatsaechliches_datum = Column(Date)  # actual_date
    tatsaechliche_zeit = Column(Time)  # actual_time
    
    # Status and outcome
    status = Column(String(50), default=PhoneCallStatus.SCHEDULED.value)
    ergebnis = Column(Text)  # outcome
    notizen = Column(Text)  # notes
    wiederholen_nach = Column(Date)  # retry_after
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    batches = relationship(
        "PhoneCallBatch",
        back_populates="phone_call",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        """Provide a string representation of the PhoneCall instance."""
        return (
            f"<PhoneCall id={self.id} therapist_id={self.therapist_id} "
            f"scheduled={self.geplantes_datum} {self.geplante_zeit} "
            f"status={self.status}>"
        )
    
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
        self.status = PhoneCallStatus.COMPLETED.value
        self.tatsaechliches_datum = actual_date or date.today()
        self.tatsaechliche_zeit = actual_time or self.geplante_zeit
        if outcome:
            self.ergebnis = outcome
        if notes:
            self.notizen = notes
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, 
                      retry_date: Optional[date] = None,
                      notes: Optional[str] = None) -> None:
        """Mark the phone call as failed.
        
        Args:
            retry_date: When to retry the call
            notes: Reason for failure
        """
        self.status = PhoneCallStatus.FAILED.value
        if retry_date:
            self.wiederholen_nach = retry_date
        if notes:
            self.notizen = notes
        self.updated_at = datetime.utcnow()
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the phone call.
        
        Args:
            reason: Reason for cancellation
        """
        self.status = PhoneCallStatus.CANCELED.value
        if reason:
            self.notizen = reason
        self.updated_at = datetime.utcnow()
    
    def is_overdue(self) -> bool:
        """Check if the scheduled call is overdue."""
        if self.status != PhoneCallStatus.SCHEDULED.value:
            return False
        return self.geplantes_datum < date.today()


class PhoneCallBatch(Base):
    """Phone call batch database model with German field names.

    This model represents a batch of patients from bundles discussed 
    in a single phone call with a therapist.
    """

    __tablename__ = "phone_call_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    phone_call_id = Column(
        Integer,
        ForeignKey("communication_service.phone_calls.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Updated foreign key to reference bundle system
    therapeut_anfrage_patient_id = Column(
        Integer,
        ForeignKey("matching_service.therapeut_anfrage_patient.id", ondelete="CASCADE"),
        nullable=True
    )
    
    priority = Column(Integer, default=1)
    discussed = Column(Boolean, default=False)
    
    # Outcome tracking - German field names
    ergebnis = Column(String(50))  # outcome
    nachverfolgung_erforderlich = Column(Boolean, default=False)  # follow_up_required
    nachverfolgung_notizen = Column(Text)  # follow_up_notes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phone_call = relationship("PhoneCall", back_populates="batches")
    
    def __repr__(self):
        """Provide a string representation of the PhoneCallBatch instance."""
        return (
            f"<PhoneCallBatch id={self.id} "
            f"phone_call_id={self.phone_call_id} "
            f"therapeut_anfrage_patient_id={self.therapeut_anfrage_patient_id}>"
        )
    
    def mark_as_discussed(self, 
                         outcome: Optional[str] = None,
                         follow_up_required: bool = False,
                         follow_up_notes: Optional[str] = None) -> None:
        """Mark this batch item as discussed during the call.
        
        Args:
            outcome: The outcome for this patient
            follow_up_required: Whether follow-up is needed
            follow_up_notes: Notes about required follow-up
        """
        self.discussed = True
        if outcome:
            self.ergebnis = outcome
        self.nachverfolgung_erforderlich = follow_up_required
        if follow_up_notes:
            self.nachverfolgung_notizen = follow_up_notes