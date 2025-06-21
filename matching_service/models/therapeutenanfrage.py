"""Therapeutenanfrage (Therapist Inquiry) database model."""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column, DateTime, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, String, Text, event, CheckConstraint
)
from sqlalchemy.orm import relationship, validates

from shared.utils.database import Base


class AntwortTyp(str, Enum):
    """Enumeration for inquiry response types."""
    
    vollstaendige_Annahme = "vollstaendige_Annahme"
    teilweise_Annahme = "teilweise_Annahme"
    vollstaendige_Ablehnung = "vollstaendige_Ablehnung"
    keine_Antwort = "keine_Antwort"


class Therapeutenanfrage(Base):
    """Therapist inquiry model.
    
    Represents an inquiry of patients sent to a therapist.
    Tracks the response and outcome of the inquiry.
    """
    
    __tablename__ = "therapeutenanfrage"
    __table_args__ = (
        CheckConstraint('anfragegroesse >= 3 AND anfragegroesse <= 6', name='anfrage_size_check'),
        CheckConstraint('angenommen_anzahl >= 0', name='accepted_count_check'),
        CheckConstraint('abgelehnt_anzahl >= 0', name='rejected_count_check'),
        CheckConstraint('keine_antwort_anzahl >= 0', name='no_response_count_check'),
        {"schema": "matching_service"}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Therapist reference - Using simple Integer instead of ForeignKey
    therapist_id = Column(
        Integer,
        nullable=False,
        index=True
    )  # References therapist_service.therapeuten.id
    
    # Timestamps (German field names)
    erstellt_datum = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    gesendet_datum = Column(DateTime, index=True)
    antwort_datum = Column(DateTime)
    
    # Response tracking (German field names)
    antworttyp = Column(
        SQLAlchemyEnum(AntwortTyp, name='antworttyp', native_enum=True),
        index=True
    )
    
    # Inquiry composition (German field names - renamed from bundle)
    anfragegroesse = Column(Integer, nullable=False)
    angenommen_anzahl = Column(Integer, nullable=False, default=0)
    abgelehnt_anzahl = Column(Integer, nullable=False, default=0)
    keine_antwort_anzahl = Column(Integer, nullable=False, default=0)
    
    # Notes (German field name)
    notizen = Column(Text)
    
    # Communication references - Using simple Integer instead of ForeignKey
    email_id = Column(
        Integer,
        index=True
    )  # References communication_service.emails.id
    
    phone_call_id = Column(
        Integer,
        index=True
    )  # References communication_service.telefonanrufe.id
    
    # Relationships
    # Note: Using string references to avoid cross-service imports
    # Therapist is in therapist_service, Email/PhoneCall in communication_service
    # These relationships work only if all models are in same SQLAlchemy session
    # Otherwise, use service layer for cross-service data access
    
    anfrage_patients = relationship(
        "TherapeutAnfragePatient",
        back_populates="therapeutenanfrage",
        cascade="all, delete-orphan",
        order_by="TherapeutAnfragePatient.position_in_anfrage"
    )
    
    def __repr__(self):
        """String representation."""
        return f"<Therapeutenanfrage therapist_id={self.therapist_id} size={self.anfragegroesse}>"
    
    # Business Logic Methods
    
    def add_patients(self, patient_searches: List[tuple]) -> None:
        """Add patients to the inquiry.
        
        Args:
            patient_searches: List of tuples (platzsuche_id, patient_id)
            
        Raises:
            ValueError: If trying to add more than 6 patients or less than 3
        """
        if len(patient_searches) < 3 or len(patient_searches) > 6:
            raise ValueError("Inquiry must contain between 3 and 6 patients")
        
        # Import here to avoid circular imports
        from .therapeut_anfrage_patient import TherapeutAnfragePatient
        
        for position, (platzsuche_id, patient_id) in enumerate(patient_searches, 1):
            anfrage_patient = TherapeutAnfragePatient(
                therapeutenanfrage_id=self.id,
                platzsuche_id=platzsuche_id,
                patient_id=patient_id,
                position_in_anfrage=position
            )
            self.anfrage_patients.append(anfrage_patient)
        
        self.anfragegroesse = len(patient_searches)
    
    def mark_as_sent(self, email_id: Optional[int] = None, phone_call_id: Optional[int] = None) -> None:
        """Mark the inquiry as sent.
        
        Args:
            email_id: ID of the email used to send the inquiry
            phone_call_id: ID of the phone call used to communicate the inquiry
        """
        self.gesendet_datum = datetime.utcnow()
        if email_id:
            self.email_id = email_id
        if phone_call_id:
            self.phone_call_id = phone_call_id
    
    def update_response(
        self,
        response_type: AntwortTyp,
        accepted_count: int = 0,
        rejected_count: int = 0,
        no_response_count: int = 0,
        notes: Optional[str] = None
    ) -> None:
        """Update the inquiry response.
        
        Args:
            response_type: Type of response received
            accepted_count: Number of accepted patients
            rejected_count: Number of rejected patients
            no_response_count: Number of patients with no response
            notes: Optional notes about the response
            
        Raises:
            ValueError: If counts don't add up to inquiry size
        """
        total = accepted_count + rejected_count + no_response_count
        if total != self.anfragegroesse:
            raise ValueError(
                f"Response counts ({total}) must equal inquiry size ({self.anfragegroesse})"
            )
        
        self.antwort_datum = datetime.utcnow()
        self.antworttyp = response_type
        self.angenommen_anzahl = accepted_count
        self.abgelehnt_anzahl = rejected_count
        self.keine_antwort_anzahl = no_response_count
        
        if notes:
            self.add_note(notes)
    
    def calculate_response_type(self) -> AntwortTyp:
        """Calculate the response type based on individual responses.
        
        Returns:
            The calculated response type
        """
        if self.angenommen_anzahl == self.anfragegroesse:
            return AntwortTyp.vollstaendige_Annahme
        elif self.angenommen_anzahl > 0:
            return AntwortTyp.teilweise_Annahme
        elif self.abgelehnt_anzahl == self.anfragegroesse:
            return AntwortTyp.vollstaendige_Ablehnung
        else:
            return AntwortTyp.keine_Antwort
    
    def get_patient_details(self) -> List[Dict[str, Any]]:
        """Get details of all patients in the inquiry.
        
        Returns:
            List of dictionaries with patient details
        """
        details = []
        for anfrage_patient in self.anfrage_patients:
            details.append({
                'position': anfrage_patient.position_in_anfrage,
                'patient_id': anfrage_patient.patient_id,
                'platzsuche_id': anfrage_patient.platzsuche_id,
                'status': anfrage_patient.status,
                'outcome': anfrage_patient.antwortergebnis
            })
        return details
    
    def get_accepted_patients(self) -> List['TherapeutAnfragePatient']:
        """Get list of accepted patients.
        
        Returns:
            List of TherapeutAnfragePatient entries that were accepted
        """
        return [ap for ap in self.anfrage_patients 
                if ap.antwortergebnis and 'angenommen' in ap.antwortergebnis]
    
    def get_rejected_patients(self) -> List['TherapeutAnfragePatient']:
        """Get list of rejected patients.
        
        Returns:
            List of TherapeutAnfragePatient entries that were rejected
        """
        return [ap for ap in self.anfrage_patients 
                if ap.antwortergebnis and 'abgelehnt' in ap.antwortergebnis]
    
    def is_response_complete(self) -> bool:
        """Check if all patient responses have been recorded.
        
        Returns:
            True if all patients have a response, False otherwise
        """
        return all(ap.antwortergebnis is not None for ap in self.anfrage_patients)
    
    def add_note(self, note: str, author: Optional[str] = None) -> None:
        """Add a timestamped note to the inquiry.
        
        Args:
            note: The note to add
            author: Optional author of the note
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        author_str = f" ({author})" if author else ""
        new_note = f"[{timestamp}{author_str}] {note}"
        
        if self.notizen:
            self.notizen += f"\n{new_note}"
        else:
            self.notizen = new_note
    
    @validates('anfragegroesse')
    def validate_anfrage_size(self, key, value):
        """Validate inquiry size is between 3 and 6.
        
        Args:
            key: The attribute key
            value: The new value
            
        Returns:
            The value if valid
            
        Raises:
            ValueError: If inquiry size is invalid
        """
        if value < 3 or value > 6:
            raise ValueError(f"Inquiry size must be between 3 and 6, got {value}")
        return value
    
    def set_cooling_period_for_therapist(self, weeks: int = 4) -> None:
        """Set cooling period for the therapist after contact.
        
        Args:
            weeks: Number of weeks for cooling period (default: 4)
        """
        # This method would typically update the therapist record
        # but since we can't import Therapist model here (circular import),
        # this should be handled by the service layer
        from datetime import timedelta
        next_contactable = datetime.utcnow() + timedelta(weeks=weeks)
        
        # Log this requirement
        self.add_note(
            f"Cooling period set until {next_contactable.strftime('%Y-%m-%d')}"
        )
    
    def days_since_sent(self) -> Optional[int]:
        """Calculate days since the inquiry was sent.
        
        Returns:
            Number of days or None if not sent yet
        """
        if not self.gesendet_datum:
            return None
        
        delta = datetime.utcnow() - self.gesendet_datum
        return delta.days
    
    def needs_follow_up(self, days_threshold: int = 7) -> bool:
        """Check if inquiry needs follow-up (e.g., phone call).
        
        Args:
            days_threshold: Number of days after which follow-up is needed
            
        Returns:
            True if follow-up is needed
        """
        if not self.gesendet_datum or self.antwort_datum:
            return False
        
        days_elapsed = self.days_since_sent()
        return days_elapsed is not None and days_elapsed >= days_threshold
    
    # Keep these property methods for backwards compatibility
    @property
    def created_date(self):
        """Backwards compatibility property."""
        return self.erstellt_datum
    
    @property
    def sent_date(self):
        """Backwards compatibility property."""
        return self.gesendet_datum
    
    @property
    def response_date(self):
        """Backwards compatibility property."""
        return self.antwort_datum