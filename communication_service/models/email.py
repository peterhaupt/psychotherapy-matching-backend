"""Email database models with patient support."""
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAlchemyEnum,
    Integer, String, Text
)

from shared.utils.database import Base


class EmailStatus(str, Enum):
    """Enumeration for email status values - fully German."""

    Entwurf = "Entwurf"
    In_Warteschlange = "In_Warteschlange"
    Wird_gesendet = "Wird_gesendet"
    Gesendet = "Gesendet"
    Fehlgeschlagen = "Fehlgeschlagen"


class Email(Base):
    """Email database model with German field names and patient support."""

    __tablename__ = "emails"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Recipients - now supports both therapist AND patient
    therapist_id = Column(Integer, nullable=True)  # Changed from nullable=False
    patient_id = Column(Integer, nullable=True)     # NEW field
    
    # Email metadata - German field names
    betreff = Column(String(255), nullable=False)  # subject
    inhalt_html = Column(Text, nullable=False)  # body_html
    inhalt_text = Column(Text, nullable=False)  # body_text
    empfaenger_email = Column(String(255), nullable=False)  # recipient_email
    empfaenger_name = Column(String(255), nullable=False)  # recipient_name
    absender_email = Column(String(255), nullable=False)  # sender_email
    absender_name = Column(String(255), nullable=False)  # sender_name
    
    # Response tracking - German field names
    antwort_erhalten = Column(Boolean, default=False)  # response_received
    antwortdatum = Column(DateTime)  # response_date
    antwortinhalt = Column(Text)  # response_content
    nachverfolgung_erforderlich = Column(Boolean, default=False)  # follow_up_required
    nachverfolgung_notizen = Column(Text)  # follow_up_notes
    
    # Status information
    status = Column(
        SQLAlchemyEnum(EmailStatus),
        default=EmailStatus.Entwurf
    )
    in_warteschlange_am = Column(DateTime)  # queued_at
    gesendet_am = Column(DateTime)  # sent_at
    fehlermeldung = Column(Text)  # error_message
    wiederholungsanzahl = Column(Integer, default=0)  # retry_count
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        """Provide a string representation of the Email instance."""
        recipient_type = "therapist" if self.therapist_id else "patient"
        recipient_id = self.therapist_id or self.patient_id
        return f"<Email id={self.id} to={recipient_type}:{recipient_id} status={self.status}>"
    
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
        """Check if this email is for a patient."""
        return self.patient_id is not None

    def is_for_therapist(self) -> bool:
        """Check if this email is for a therapist."""
        return self.therapist_id is not None
    
    def mark_as_sent(self) -> None:
        """Mark email as sent with timestamp."""
        self.status = EmailStatus.Gesendet
        self.gesendet_am = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark email as failed with error message."""
        self.status = EmailStatus.Fehlgeschlagen
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
            self.status == EmailStatus.Gesendet and 
            not self.antwort_erhalten
        )
    
    def days_since_sent(self) -> int:
        """Calculate days since the email was sent."""
        if not self.gesendet_am:
            return 0
        return (datetime.utcnow() - self.gesendet_am).days