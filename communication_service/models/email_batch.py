"""Email batch database models."""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from shared.utils.database import Base


class EmailBatch(Base):
    """Email batch database model with German field names.
    
    This model represents the relationship between emails and bundle patients,
    allowing multiple patients from bundles to be grouped into a single email.
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
    
    # Updated foreign key to reference bundle system
    therapeut_anfrage_patient_id = Column(
        Integer,
        ForeignKey("matching_service.therapeut_anfrage_patient.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Batch metadata
    priority = Column(Integer, default=1)  # Higher numbers = higher priority
    included = Column(Boolean, default=True)  # Flag to indicate if the request was included in the email
    
    # Response tracking - German field names
    antwortergebnis = Column(String(50))  # response_outcome: e.g., "angenommen", "abgelehnt", "nachverfolgung_erforderlich"
    antwortnotizen = Column(Text)  # response_notes
    
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
            f"therapeut_anfrage_patient_id={self.therapeut_anfrage_patient_id}>"
        )
    
    def mark_response(self, outcome: str, notes: str = None) -> None:
        """Mark the response for this batch item.
        
        Args:
            outcome: The outcome (angenommen, abgelehnt, etc.)
            notes: Optional notes about the response
        """
        self.antwortergebnis = outcome
        if notes:
            self.antwortnotizen = notes
        self.updated_at = datetime.utcnow()
    
    def is_accepted(self) -> bool:
        """Check if this patient was accepted by the therapist."""
        return self.antwortergebnis == "angenommen"
    
    def is_rejected(self) -> bool:
        """Check if this patient was rejected by the therapist."""
        return self.antwortergebnis == "abgelehnt"