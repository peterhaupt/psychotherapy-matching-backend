"""Email database models."""
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAlchemyEnum,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB

from shared.utils.database import Base


class EmailStatus(str, Enum):
    """Enumeration for email status values."""

    DRAFT = "entwurf"
    QUEUED = "in_warteschlange"
    SENDING = "wird_gesendet"
    SENT = "gesendet"
    FAILED = "fehlgeschlagen"


class Email(Base):
    """Email database model."""

    __tablename__ = "emails"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Email metadata
    therapist_id = Column(Integer, nullable=False)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False)
    
    # Placement requests associated with this email (will be replaced by batches)
    placement_request_ids = Column(JSONB)
    
    # Batch identifier
    batch_id = Column(String(50))
    
    # Response tracking
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_content = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    
    # Status information
    status = Column(
        SQLAlchemyEnum(EmailStatus),
        default=EmailStatus.DRAFT
    )
    queued_at = Column(DateTime)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        """Provide a string representation of the Email instance."""
        return f"<Email id={self.id} to={self.recipient_email} status={self.status}>"