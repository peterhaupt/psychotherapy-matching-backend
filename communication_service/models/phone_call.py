"""Phone call database models."""
from datetime import datetime
from enum import Enum

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
    """Phone call database model.

    This model represents a scheduled or completed phone call to a therapist,
    including call details, status tracking, and outcomes.
    """

    __tablename__ = "phone_calls"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=5)
    actual_date = Column(Date)
    actual_time = Column(Time)
    status = Column(String(50), default=PhoneCallStatus.SCHEDULED.value)
    outcome = Column(Text)
    notes = Column(Text)
    retry_after = Column(Date)
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
            f"scheduled={self.scheduled_date} {self.scheduled_time} "
            f"status={self.status}>"
        )


class PhoneCallBatch(Base):
    """Phone call batch database model.

    This model represents a batch of placement requests discussed in a single
    phone call with a therapist.
    """

    __tablename__ = "phone_call_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    phone_call_id = Column(
        Integer,
        ForeignKey("communication_service.phone_calls.id", ondelete="CASCADE"),
        nullable=False
    )
    placement_request_id = Column(
        Integer,
        ForeignKey("matching_service.placement_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    priority = Column(Integer, default=1)
    discussed = Column(Boolean, default=False)
    outcome = Column(String(50))
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phone_call = relationship("PhoneCall", back_populates="batches")
    
    def __repr__(self):
        """Provide a string representation of the PhoneCallBatch instance."""
        return (
            f"<PhoneCallBatch id={self.id} "
            f"phone_call_id={self.phone_call_id} "
            f"placement_request_id={self.placement_request_id}>"
        )