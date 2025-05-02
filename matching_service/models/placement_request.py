"""Placement request database models."""
from datetime import date
from enum import Enum

from sqlalchemy import (
    Column, Date, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, Text
)

from shared.utils.database import Base


class PlacementRequestStatus(str, Enum):
    """Enumeration for placement request status values."""

    OPEN = "offen"
    IN_PROGRESS = "in_bearbeitung"
    REJECTED = "abgelehnt"
    ACCEPTED = "angenommen"


class PlacementRequest(Base):
    """Placement request database model.

    This model represents a matching request between a patient and a therapist,
    including the status of the request, contact history, and response tracking.
    """

    __tablename__ = "placement_requests"
    __table_args__ = {"schema": "matching_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # References
    patient_id = Column(Integer, nullable=False)
    therapist_id = Column(Integer, nullable=False)
    
    # Status tracking
    status = Column(
        SQLAlchemyEnum(PlacementRequestStatus),
        default=PlacementRequestStatus.OPEN
    )
    
    # Contact tracking
    created_at = Column(Date, default=date.today)
    email_contact_date = Column(Date)
    phone_contact_date = Column(Date)
    
    # Response tracking
    response = Column(Text)
    response_date = Column(Date)
    next_contact_after = Column(Date)  # For rejected requests that can be retried
    
    # Additional metadata
    priority = Column(Integer, default=1)  # Higher numbers = higher priority
    notes = Column(Text)

    def __repr__(self):
        """Provide a string representation of the PlacementRequest instance."""
        return (
            f"<PlacementRequest patient_id={self.patient_id} "
            f"therapist_id={self.therapist_id} status={self.status}>"
        )