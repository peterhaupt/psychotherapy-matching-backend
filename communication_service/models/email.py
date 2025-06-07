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

    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Email(Base):
    """Email database model with German field names."""

    __tablename__ = "emails"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Email metadata - German field names
    therapist_id = Column(Integer, nullable=False)
    betreff = Column(String(255), nullable=False)  # subject
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=False)
    empfaenger_email = Column(String(255), nullable=False)  # recipient_email
    empfaenger_name = Column(String(255), nullable=False)  # recipient_name
    absender_email = Column(String(255), nullable=False)  # sender_email
    absender_name = Column(String(255), nullable=False)  # sender_name
    
    # Legacy field - will be removed in future
    placement_request_ids = Column(JSONB)
    
    # Batch identifier
    batch_id = Column(String(50))
    
    # Response tracking - German field names
    antwort_erhalten = Column(Boolean, default=False)  # response_received
    antwortdatum = Column(DateTime)  # response_date
    antwortinhalt = Column(Text)  # response_content
    nachverfolgung_erforderlich = Column(Boolean, default=False)  # follow_up_required
    nachverfolgung_notizen = Column(Text)  # follow_up_notes
    
    # Status information
    status = Column(
        SQLAlchemyEnum(EmailStatus),
        default=EmailStatus.DRAFT
    )
    queued_at = Column(DateTime)
    sent_at = Column(DateTime)
    fehlermeldung = Column(Text)  # error_message
    wiederholungsanzahl = Column(Integer, default=0)  # retry_count
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        """Provide a string representation of the Email instance."""
        return f"<Email id={self.id} to={self.empfaenger_email} status={self.status}>"
    
    def mark_as_sent(self) -> None:
        """Mark email as sent with timestamp."""
        self.status = EmailStatus.SENT
        self.sent_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark email as failed with error message."""
        self.status = EmailStatus.FAILED
        self.fehlermeldung = error_message
        self.wiederholungsanzahl += 1
    
    def record_response(self, response_content: str = None) -> None:
        """Record that a response was received."""
        self.antwort_erhalten = True
        self.antwortdatum = datetime.utcnow()
        if response_content:
            self.antwortinhalt = response_content
    
    def is_awaiting_response(self) -> bool:
        """Check if email is sent but hasn't received a response."""
        return (
            self.status == EmailStatus.SENT and 
            not self.antwort_erhalten
        )
    
    def days_since_sent(self) -> int:
        """Calculate days since the email was sent."""
        if not self.sent_at:
            return 0
        return (datetime.utcnow() - self.sent_at).days