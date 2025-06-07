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


class SearchStatus(str, Enum):
    """Enumeration for patient search status values."""
    
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Platzsuche(Base):
    """Patient search tracking model.
    
    Represents an ongoing search for therapy placement for a patient.
    Tracks excluded therapists, contact attempts, and search status.
    """
    
    __tablename__ = "platzsuche"
    __table_args__ = {"schema": "matching_service"}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Patient reference
    patient_id = Column(
        Integer,
        ForeignKey("patient_service.patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Search status
    status = Column(
        SQLAlchemyEnum(SearchStatus),
        nullable=False,
        default=SearchStatus.ACTIVE,
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
    
    # Notes (German field name)
    notizen = Column(Text)
    
    # Relationships
    # Note: Using string reference to avoid cross-service imports
    # The Patient model is in patient_service
    # This relationship can be used if models are in same session
    # Otherwise, use service layer for cross-service data
    
    bundle_entries = relationship(
        "TherapeutAnfragePatient",
        back_populates="platzsuche",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        """String representation."""
        return f"<Platzsuche patient_id={self.patient_id} status={self.status}>"
    
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
    
    def mark_successful(self, vermittlung_datum: Optional[datetime] = None) -> None:
        """Mark the search as successful.
        
        Args:
            vermittlung_datum: Date of successful placement (defaults to now)
        """
        self.status = SearchStatus.SUCCESSFUL
        self.erfolgreiche_vermittlung_datum = vermittlung_datum or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def pause_search(self, reason: Optional[str] = None) -> None:
        """Pause the search.
        
        Args:
            reason: Optional reason for pausing
        """
        self.status = SearchStatus.PAUSED
        self.updated_at = datetime.utcnow()
        if reason and self.notizen:
            self.notizen += f"\n\nPaused: {reason}"
        elif reason:
            self.notizen = f"Paused: {reason}"
    
    def resume_search(self) -> None:
        """Resume a paused search."""
        if self.status == SearchStatus.PAUSED:
            self.status = SearchStatus.ACTIVE
            self.updated_at = datetime.utcnow()
            if self.notizen:
                self.notizen += "\n\nSearch resumed"
    
    def cancel_search(self, reason: Optional[str] = None) -> None:
        """Cancel the search.
        
        Args:
            reason: Optional reason for cancellation
        """
        self.status = SearchStatus.CANCELLED
        self.updated_at = datetime.utcnow()
        if reason and self.notizen:
            self.notizen += f"\n\nCancelled: {reason}"
        elif reason:
            self.notizen = f"Cancelled: {reason}"
    
    def get_active_bundle_count(self) -> int:
        """Get count of active bundles this search is part of.
        
        Returns:
            Number of active bundles
        """
        if not self.bundle_entries:
            return 0
        
        return sum(1 for entry in self.bundle_entries 
                  if entry.status == "pending")
    
    def get_total_bundle_count(self) -> int:
        """Get total count of bundles this search has been part of.
        
        Returns:
            Total number of bundles
        """
        return len(self.bundle_entries) if self.bundle_entries else 0
    
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
                SearchStatus.ACTIVE: [SearchStatus.SUCCESSFUL, SearchStatus.PAUSED, SearchStatus.CANCELLED],
                SearchStatus.PAUSED: [SearchStatus.ACTIVE, SearchStatus.CANCELLED],
                SearchStatus.SUCCESSFUL: [],  # Terminal state
                SearchStatus.CANCELLED: []    # Terminal state
            }
            
            if new_status not in allowed_transitions.get(current, []):
                raise ValueError(
                    f"Invalid status transition from {current} to {new_status}"
                )
        
        return new_status
    
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