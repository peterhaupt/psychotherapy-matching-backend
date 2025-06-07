"""Phone call database models."""
from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, 
    String, Text, Time
)

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