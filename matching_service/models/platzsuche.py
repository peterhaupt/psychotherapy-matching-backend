"""Platzsuche (Patient Search) database model."""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Set

from sqlalchemy import (
    Column, DateTime, Enum as SQLAlchemyEnum,
    ForeignKey, Integer, String, Text, event
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates

from shared.utils.database import Base


class SuchStatus(str, Enum):
    """Enumeration for patient search status values."""
    
    aktiv = "aktiv"
    erfolgreich = "erfolgreich"
    pausiert = "pausiert"
    abgebrochen = "abgebrochen"


class Platzsuche(Base):
    """Patient search tracking model.
    
    Represents an ongoing search for therapy placement for a patient.
    Tracks excluded therapists, contact attempts, and search status.
    """
    
    __tablename__ = "platzsuche"
    __table_args__ = {"schema": "matching_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Patient reference - Using simple Integer instead of ForeignKey
    patient_id = Column(
        Integer,
        nullable=False,
        index=True
    )  # References patient_service.patienten.id
    
    # Search status
    status = Column(
        SQLAlchemyEnum(SuchStatus, name='suchstatus', native_enum=True),
        nullable=False,
        default=SuchStatus.aktiv,
        index=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Excluded therapists (German field name as per database)
    ausgeschlossene_therapeuten = Column(
        JSONB,
        nullable=False,
        default=list
    )
    
    # Contact tracking (German field names)
    gesamt_angeforderte_kontakte = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Success tracking (German field name)
    erfolgreiche_vermittlung_datum = Column(DateTime)
    
    # NEW: Track the therapist who accepted the patient
    vermittelter_therapeut_id = Column(
        Integer,
        nullable=True,
        index=True
    )  # References therapist_service.therapeuten.id
    
    # Notes (German field name)
    notizen = Column(Text)
    
    # Relationships
    # Note: Using string reference to avoid cross-service imports
    # The Patient model is in patient_service
    # This relationship can be used if models are in same session
    # Otherwise, use service layer for cross-service data
    
    anfrage_entries = relationship(
        "TherapeutAnfragePatient",
        back_populates="platzsuche",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        """String representation."""
        therapeut_info = f" therapeut={self.vermittelter_therapeut_id}" if self.vermittelter_therapeut_id else ""
        return f"<Platzsuche patient_id={self.patient_id} status={self.status}{therapeut_info}>"
    
    # Business Logic Methods
    
    def exclude_therapist(self, therapist_id: int, reason: Optional[str] = None) -> None:
        """Add a therapist to the exclusion list.
        
        Args:
            therapist_id: ID of the therapist to exclude
            reason: Optional reason for exclusion
        """
        if self.ausgeschlossene_therapeuten is None:
            self.ausgeschlossene_therapeuten = []
        
        # Ensure therapist_id is not already in the list
        current_ids = {entry if isinstance(entry, int) else entry.get('id') 
                      for entry in self.ausgeschlossene_therapeuten}
        
        if therapist_id not in current_ids:
            exclusion_entry = {
                'id': therapist_id,
                'excluded_at': datetime.utcnow().isoformat(),
                'reason': reason
            }
            self.ausgeschlossene_therapeuten.append(exclusion_entry)
    
    def is_therapist_excluded(self, therapist_id: int) -> bool:
        """Check if a therapist is in the exclusion list.
        
        Args:
            therapist_id: ID of the therapist to check
            
        Returns:
            True if therapist is excluded, False otherwise
        """
        if not self.ausgeschlossene_therapeuten:
            return False
        
        excluded_ids = {entry if isinstance(entry, int) else entry.get('id') 
                       for entry in self.ausgeschlossene_therapeuten}
        return therapist_id in excluded_ids
    
    def get_excluded_therapist_ids(self) -> Set[int]:
        """Get set of all excluded therapist IDs.
        
        Returns:
            Set of therapist IDs that are excluded
        """
        if not self.ausgeschlossene_therapeuten:
            return set()
        
        return {entry if isinstance(entry, int) else entry.get('id') 
                for entry in self.ausgeschlossene_therapeuten}
    
    def update_contact_count(self, additional_contacts: int) -> None:
        """Update the total requested contacts count.
        
        Args:
            additional_contacts: Number of additional contacts requested
        """
        self.gesamt_angeforderte_kontakte += additional_contacts
        self.updated_at = datetime.utcnow()
    
    def mark_successful(self, vermittlung_datum: Optional[datetime] = None, 
                       therapist_id: Optional[int] = None) -> None:
        """Mark the search as successful.
        
        Args:
            vermittlung_datum: Date of successful placement (defaults to now)
            therapist_id: ID of the therapist who accepted the patient
        
        Raises:
            ValueError: If therapist_id is not provided when vermittelter_therapeut_id is not set
        """
        # Check if therapist_id needs to be set
        if not self.vermittelter_therapeut_id and not therapist_id:
            raise ValueError("Cannot mark as successful without therapist_id")
        
        # Set therapist if provided
        if therapist_id:
            self.set_vermittelter_therapeut(therapist_id)
        
        self.status = SuchStatus.erfolgreich
        self.erfolgreiche_vermittlung_datum = vermittlung_datum or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_vermittelter_therapeut(self, therapist_id: int) -> None:
        """Set the therapist who will treat the patient.
        
        Args:
            therapist_id: ID of the therapist
            
        Raises:
            ValueError: If trying to change therapist when status is already erfolgreich
        """
        if self.status == SuchStatus.erfolgreich and self.vermittelter_therapeut_id and \
           self.vermittelter_therapeut_id != therapist_id:
            raise ValueError("Cannot change vermittelter_therapeut_id after successful placement")
        
        self.vermittelter_therapeut_id = therapist_id
        self.updated_at = datetime.utcnow()
    
    def can_change_therapeut(self) -> bool:
        """Check if the therapist can be changed.
        
        Returns:
            True if therapist can be changed, False if status is already erfolgreich
        """
        return self.status != SuchStatus.erfolgreich or self.vermittelter_therapeut_id is None
    
    def get_vermittelter_therapeut_id(self) -> Optional[int]:
        """Get the ID of the assigned therapist.
        
        Returns:
            Therapist ID or None if not assigned
        """
        return self.vermittelter_therapeut_id
    
    def pause_search(self, reason: Optional[str] = None) -> None:
        """Pause the search.
        
        Args:
            reason: Optional reason for pausing
        """
        self.status = SuchStatus.pausiert
        self.updated_at = datetime.utcnow()
        if reason and self.notizen:
            self.notizen += f"\n\nPaused: {reason}"
        elif reason:
            self.notizen = f"Paused: {reason}"
    
    def resume_search(self) -> None:
        """Resume a paused search."""
        if self.status == SuchStatus.pausiert:
            self.status = SuchStatus.aktiv
            self.updated_at = datetime.utcnow()
            if self.notizen:
                self.notizen += "\n\nSearch resumed"
    
    def cancel_search(self, reason: Optional[str] = None) -> None:
        """Cancel the search.
        
        Args:
            reason: Optional reason for cancellation
        """
        self.status = SuchStatus.abgebrochen
        self.updated_at = datetime.utcnow()
        if reason and self.notizen:
            self.notizen += f"\n\nCancelled: {reason}"
        elif reason:
            self.notizen = f"Cancelled: {reason}"
    
    def get_active_anfrage_count(self) -> int:
        """Get count of active inquiries this search is part of.
        
        Returns:
            Number of active inquiries
        """
        if not self.anfrage_entries:
            return 0
        
        return sum(1 for entry in self.anfrage_entries 
                  if entry.status == "anstehend")
    
    def get_total_anfrage_count(self) -> int:
        """Get total count of inquiries this search has been part of.
        
        Returns:
            Total number of inquiries
        """
        return len(self.anfrage_entries) if self.anfrage_entries else 0
    
    @validates('status')
    def validate_status_transition(self, key, new_status):
        """Validate status transitions.
        
        Args:
            key: The attribute key ('status')
            new_status: The new status value
            
        Returns:
            The new status if valid
            
        Raises:
            ValueError: If the transition is not allowed
        """
        if hasattr(self, 'status') and self.status:
            current = self.status
            
            # Define allowed transitions
            allowed_transitions = {
                SuchStatus.aktiv: [SuchStatus.erfolgreich, SuchStatus.pausiert, SuchStatus.abgebrochen],
                SuchStatus.pausiert: [SuchStatus.aktiv, SuchStatus.abgebrochen],
                SuchStatus.erfolgreich: [],  # Terminal state
                SuchStatus.abgebrochen: []    # Terminal state
            }
            
            if new_status not in allowed_transitions.get(current, []):
                raise ValueError(
                    f"Invalid status transition from {current} to {new_status}"
                )
            
            # Additional validation: require therapist when marking as successful
            if new_status == SuchStatus.erfolgreich and not self.vermittelter_therapeut_id:
                raise ValueError(
                    "Cannot mark as erfolgreich without vermittelter_therapeut_id"
                )
        
        return new_status
    
    @validates('vermittelter_therapeut_id')
    def validate_therapist_change(self, key, new_therapist_id):
        """Validate changes to vermittelter_therapeut_id.
        
        Args:
            key: The attribute key ('vermittelter_therapeut_id')
            new_therapist_id: The new therapist ID
            
        Returns:
            The new therapist ID if valid
            
        Raises:
            ValueError: If trying to change after successful placement
        """
        # Allow setting if not yet set
        if not hasattr(self, 'vermittelter_therapeut_id') or self.vermittelter_therapeut_id is None:
            return new_therapist_id
        
        # Allow if status is not erfolgreich
        if hasattr(self, 'status') and self.status != SuchStatus.erfolgreich:
            return new_therapist_id
        
        # If status is erfolgreich and trying to change to a different value
        if self.vermittelter_therapeut_id != new_therapist_id:
            raise ValueError(
                "Cannot change vermittelter_therapeut_id after successful placement"
            )
        
        return new_therapist_id
    
    def add_note(self, note: str, author: Optional[str] = None) -> None:
        """Add a timestamped note to the search.
        
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