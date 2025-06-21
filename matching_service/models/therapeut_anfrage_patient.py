"""TherapeutAnfragePatient (Inquiry Composition) database model."""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, String, Text, UniqueConstraint, event
)
from sqlalchemy.orm import relationship, validates

from shared.utils.database import Base


class AnfragePatientStatus(str, Enum):
    """Enumeration for patient status within an inquiry."""
    
    anstehend = "anstehend"
    angenommen = "angenommen"
    abgelehnt = "abgelehnt"
    keine_antwort = "keine_antwort"


class PatientenErgebnis(str, Enum):
    """Enumeration for patient response outcomes."""
    
    angenommen = "angenommen"
    abgelehnt_Kapazitaet = "abgelehnt_Kapazitaet"
    abgelehnt_nicht_geeignet = "abgelehnt_nicht_geeignet"
    abgelehnt_sonstiges = "abgelehnt_sonstiges"
    nicht_erschienen = "nicht_erschienen"
    in_Sitzungen = "in_Sitzungen"


class TherapeutAnfragePatient(Base):
    """Inquiry composition model.
    
    Links patients to therapist inquiries and tracks
    individual patient outcomes within the inquiry.
    """
    
    __tablename__ = "therapeut_anfrage_patient"
    __table_args__ = (
        UniqueConstraint(
            'therapeutenanfrage_id', 
            'platzsuche_id',
            name='uq_therapeut_anfrage_patient_anfrage_search'
        ),
        {"schema": "matching_service"}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Inquiry reference
    therapeutenanfrage_id = Column(
        Integer,
        ForeignKey("matching_service.therapeutenanfrage.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Search reference
    platzsuche_id = Column(
        Integer,
        ForeignKey("matching_service.platzsuche.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Patient reference
    patient_id = Column(
        Integer,
        ForeignKey("patient_service.patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Position tracking (German field name - renamed from bundle)
    position_in_anfrage = Column(Integer, nullable=False)
    
    # Status tracking
    status = Column(
        SQLAlchemyEnum(AnfragePatientStatus, name='anfrage_patient_status', native_enum=True),
        nullable=False,
        default=AnfragePatientStatus.anstehend,
        index=True
    )
    
    # Outcome tracking (German field names)
    antwortergebnis = Column(SQLAlchemyEnum(PatientenErgebnis, name='patientenergebnis', native_enum=True))
    antwortnotizen = Column(Text)
    
    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    therapeutenanfrage = relationship(
        "Therapeutenanfrage",
        back_populates="anfrage_patients"
    )
    
    platzsuche = relationship(
        "Platzsuche",
        back_populates="anfrage_entries"
    )
    
    # Note: Patient relationship removed due to cross-service boundary
    # Use service layer to fetch patient data when needed
    
    def __repr__(self):
        """String representation."""
        return (
            f"<TherapeutAnfragePatient "
            f"anfrage={self.therapeutenanfrage_id} "
            f"patient={self.patient_id} "
            f"status={self.status}>"
        )
    
    # Business Logic Methods
    
    def update_outcome(
        self,
        outcome: PatientenErgebnis,
        notes: Optional[str] = None
    ) -> None:
        """Update the patient's outcome in this inquiry.
        
        Args:
            outcome: The outcome of the therapist's response for this patient
            notes: Optional notes about the outcome
        """
        self.antwortergebnis = outcome
        
        # Update status based on outcome
        if outcome == PatientenErgebnis.angenommen:
            self.status = AnfragePatientStatus.angenommen
        elif outcome in [PatientenErgebnis.abgelehnt_Kapazitaet, 
                        PatientenErgebnis.abgelehnt_nicht_geeignet,
                        PatientenErgebnis.abgelehnt_sonstiges]:
            self.status = AnfragePatientStatus.abgelehnt
        elif outcome == PatientenErgebnis.nicht_erschienen:
            self.status = AnfragePatientStatus.keine_antwort
            
        if notes:
            self.add_outcome_note(notes)
    
    def mark_accepted(self, notes: Optional[str] = None) -> None:
        """Mark this patient as accepted by the therapist.
        
        Args:
            notes: Optional acceptance notes
        """
        self.status = AnfragePatientStatus.angenommen
        self.antwortergebnis = PatientenErgebnis.angenommen
        if notes:
            self.add_outcome_note(notes)
    
    def mark_rejected(
        self,
        reason: PatientenErgebnis,
        notes: Optional[str] = None
    ) -> None:
        """Mark this patient as rejected by the therapist.
        
        Args:
            reason: The reason for rejection (must be a rejection outcome)
            notes: Optional rejection notes
            
        Raises:
            ValueError: If reason is not a rejection outcome
        """
        rejection_reasons = [
            PatientenErgebnis.abgelehnt_Kapazitaet,
            PatientenErgebnis.abgelehnt_nicht_geeignet,
            PatientenErgebnis.abgelehnt_sonstiges
        ]
        
        if reason not in rejection_reasons:
            raise ValueError(f"Invalid rejection reason: {reason}")
        
        self.status = AnfragePatientStatus.abgelehnt
        self.antwortergebnis = reason
        if notes:
            self.add_outcome_note(notes)
    
    def mark_no_response(self, notes: Optional[str] = None) -> None:
        """Mark this patient as having no response from therapist.
        
        Args:
            notes: Optional notes
        """
        self.status = AnfragePatientStatus.keine_antwort
        if notes:
            self.add_outcome_note(notes)
    
    def mark_in_sessions(self, notes: Optional[str] = None) -> None:
        """Mark this patient as being in trial sessions.
        
        Args:
            notes: Optional notes about the sessions
        """
        self.antwortergebnis = PatientenErgebnis.in_Sitzungen
        if notes:
            self.add_outcome_note(notes)
    
    def is_accepted(self) -> bool:
        """Check if this patient was accepted.
        
        Returns:
            True if patient was accepted
        """
        return self.status == AnfragePatientStatus.angenommen
    
    def is_rejected(self) -> bool:
        """Check if this patient was rejected.
        
        Returns:
            True if patient was rejected
        """
        return self.status == AnfragePatientStatus.abgelehnt
    
    def is_pending(self) -> bool:
        """Check if this patient's status is still pending.
        
        Returns:
            True if status is pending
        """
        return self.status == AnfragePatientStatus.anstehend
    
    def has_outcome(self) -> bool:
        """Check if this patient has any outcome recorded.
        
        Returns:
            True if an outcome has been recorded
        """
        return self.antwortergebnis is not None
    
    def add_outcome_note(self, note: str) -> None:
        """Add a note about the outcome.
        
        Args:
            note: The note to add
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"
        
        if self.antwortnotizen:
            self.antwortnotizen += f"\n{new_note}"
        else:
            self.antwortnotizen = new_note
    
    def get_therapist_id(self) -> Optional[int]:
        """Get the therapist ID from the parent inquiry.
        
        Returns:
            Therapist ID or None if relationships not loaded
        """
        if self.therapeutenanfrage:
            return self.therapeutenanfrage.therapist_id
        return None
    
    def get_anfrage_size(self) -> Optional[int]:
        """Get the size of the parent inquiry.
        
        Returns:
            Inquiry size or None if relationships not loaded
        """
        if self.therapeutenanfrage:
            return self.therapeutenanfrage.anfragegroesse
        return None
    
    def get_anfrage_position_info(self) -> str:
        """Get a string describing this patient's position in the inquiry.
        
        Returns:
            String like "Position 2 of 5"
        """
        anfrage_size = self.get_anfrage_size()
        if anfrage_size:
            return f"Position {self.position_in_anfrage} of {anfrage_size}"
        return f"Position {self.position_in_anfrage}"
    
    @validates('position_in_anfrage')
    def validate_position(self, key, value):
        """Validate position is positive.
        
        Args:
            key: The attribute key
            value: The new value
            
        Returns:
            The value if valid
            
        Raises:
            ValueError: If position is invalid
        """
        if value < 1:
            raise ValueError(f"Position must be >= 1, got {value}")
        if value > 6:  # Max inquiry size
            raise ValueError(f"Position must be <= 6 (max inquiry size), got {value}")
        return value
    
    @validates('status')
    def validate_status_transition(self, key, new_status):
        """Validate status transitions.
        
        Args:
            key: The attribute key
            new_status: The new status value
            
        Returns:
            The new status if valid
        """
        # Pending can transition to any status
        # Other statuses are generally final, but we'll allow updates
        # for flexibility (e.g., correcting mistakes)
        return new_status
    
    def should_exclude_therapist(self) -> bool:
        """Determine if the therapist should be excluded based on outcome.
        
        Returns:
            True if therapist should be added to patient's exclusion list
        """
        # Exclude if explicitly rejected or if patient didn't show up
        exclude_outcomes = [
            PatientenErgebnis.abgelehnt_nicht_geeignet,
            PatientenErgebnis.nicht_erschienen
        ]
        return self.antwortergebnis in exclude_outcomes
    
    def create_conflict_with(self, other_anfrage_id: int) -> dict:
        """Create a conflict record when patient is accepted in multiple inquiries.
        
        Args:
            other_anfrage_id: ID of the other inquiry where patient was accepted
            
        Returns:
            Dictionary with conflict information
        """
        return {
            'patient_id': self.patient_id,
            'platzsuche_id': self.platzsuche_id,
            'anfrage_1_id': self.therapeutenanfrage_id,
            'anfrage_2_id': other_anfrage_id,
            'detected_at': datetime.utcnow().isoformat()
        }