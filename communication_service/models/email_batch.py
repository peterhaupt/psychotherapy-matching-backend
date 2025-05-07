"""Email batch database models."""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from shared.utils.database import Base


class EmailBatch(Base):
    """Email batch database model.
    
    This model represents the relationship between emails and placement requests,
    allowing multiple placement requests to be grouped into a single email.
    """

    __tablename__ = "email_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    email_id = Column(
        Integer,
        ForeignKey("communication_service.emails.id", ondelete="CASCADE"),
        nullable=False
    )
    placement_request_id = Column(
        Integer,
        ForeignKey("matching_service.placement_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Batch metadata
    priority = Column(Integer, default=1)  # Higher numbers = higher priority
    included = Column(Boolean, default=True)  # Flag to indicate if the request was included in the email
    
    # Response tracking
    response_outcome = Column(String(50))  # e.g., "accepted", "rejected", "needs_follow_up"
    response_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Define relationships
    email = relationship(
        "Email",
        backref="batches",
        foreign_keys=[email_id]
    )
    
    def __repr__(self):
        """Provide a string representation of the EmailBatch instance."""
        return (
            f"<EmailBatch id={self.id} email_id={self.email_id} "
            f"placement_request_id={self.placement_request_id}>"
        )