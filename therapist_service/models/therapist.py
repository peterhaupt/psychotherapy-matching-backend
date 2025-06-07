"""Therapist database models."""
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Boolean, Column, Date, Enum as SQLAlchemyEnum,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB

from shared.utils.database import Base


class TherapistStatus(str, Enum):
    """Enumeration for therapist status values."""

    ACTIVE = "aktiv"
    BLOCKED = "gesperrt"
    INACTIVE = "inaktiv"


class Therapist(Base):
    """Therapist database model.

    This model represents a therapist in the psychotherapy matching platform,
    including personal information, professional details, availability,
    bundle preferences, and contact history.
    """

    __tablename__ = "therapists"
    __table_args__ = {"schema": "therapist_service"}

    id = Column(Integer, primary_key=True, index=True)

    # Personal Information
    anrede = Column(String(10))
    titel = Column(String(20))
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    strasse = Column(String(255))
    plz = Column(String(10))
    ort = Column(String(100))
    telefon = Column(String(50))
    fax = Column(String(50))
    email = Column(String(255))
    webseite = Column(String(255))

    # Professional Information
    kassensitz = Column(Boolean, default=True)
    geschlecht = Column(String(20))  # Derived from anrede or explicitly set
    telefonische_erreichbarkeit = Column(JSONB)  # Structure of availability times
    fremdsprachen = Column(JSONB)  # List of languages
    psychotherapieverfahren = Column(JSONB)  # List of therapy methods
    zusatzqualifikationen = Column(Text)
    besondere_leistungsangebote = Column(Text)

    # Contact History
    letzter_kontakt_email = Column(Date)
    letzter_kontakt_telefon = Column(Date)
    letztes_persoenliches_gespraech = Column(Date)

    # Availability (German field names)
    potenziell_verfuegbar = Column(Boolean, default=False)
    potenziell_verfuegbar_notizen = Column(Text)

    # Bundle System Fields (all using German names)
    naechster_kontakt_moeglich = Column(Date)  # Cooling period enforcement
    bevorzugte_diagnosen = Column(JSONB)  # List of preferred ICD-10 codes
    alter_min = Column(Integer)  # Minimum patient age preference
    alter_max = Column(Integer)  # Maximum patient age preference
    geschlechtspraeferenz = Column(String(50))  # Preferred patient gender
    arbeitszeiten = Column(JSONB)  # Working hours structure
    bevorzugt_gruppentherapie = Column(Boolean, default=False)  # Prefers group therapy

    # Status Information
    status = Column(
        SQLAlchemyEnum(TherapistStatus),
        default=TherapistStatus.ACTIVE
    )
    sperrgrund = Column(Text)
    sperrdatum = Column(Date)

    # Timestamps
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)

    def __repr__(self):
        """Provide a string representation of the Therapist instance."""
        return f"<Therapist {self.titel or ''} {self.vorname} {self.nachname}>"
    
    def is_contactable(self) -> bool:
        """Check if therapist can be contacted (not in cooling period).
        
        Returns:
            Boolean indicating if therapist can be contacted today
        """
        if self.naechster_kontakt_moeglich is None:
            return True
        return date.today() >= self.naechster_kontakt_moeglich
    
    def set_cooling_period(self, weeks: int = 4) -> None:
        """Set cooling period for this therapist.
        
        Args:
            weeks: Number of weeks for cooling period (default: 4)
        """
        self.naechster_kontakt_moeglich = date.today() + timedelta(weeks=weeks)
    
    def get_available_slots(self, date_obj: Optional[date] = None) -> Dict[str, List[Dict[str, str]]]:
        """Get available time slots for a given date.
        
        Args:
            date_obj: Optional date to filter slots (default: all slots)
            
        Returns:
            Dictionary of day -> list of time slots
        """
        availability = self.telefonische_erreichbarkeit or {}
        
        if date_obj is None:
            return availability
            
        day_name = date_obj.strftime("%A").lower()
        return {day_name: availability.get(day_name, [])}
    
    def is_available_at(self, date_obj: date, time_str: str) -> bool:
        """Check if therapist is available at a specific date and time.
        
        Args:
            date_obj: Date to check
            time_str: Time string in format "HH:MM"
            
        Returns:
            Boolean indicating if therapist is available
        """
        day_name = date_obj.strftime("%A").lower()
        day_slots = (self.telefonische_erreichbarkeit or {}).get(day_name, [])
        
        for slot in day_slots:
            if slot.get("start", "") <= time_str <= slot.get("end", ""):
                return True
                
        return False
    
    def get_next_available_slot(self, 
                               start_date: date = None, 
                               min_duration_minutes: int = 5) -> Optional[Dict[str, Any]]:
        """Find the next available time slot starting from a given date.
        
        Args:
            start_date: Date to start looking from (default: today)
            min_duration_minutes: Minimum required duration in minutes
            
        Returns:
            Dict with date, start and end time, or None if no slot found
        """
        if start_date is None:
            start_date = date.today()
            
        # Check for 7 days starting from start_date
        for day_offset in range(7):
            check_date = start_date + timedelta(days=day_offset)
            day_name = check_date.strftime("%A").lower()
            day_slots = (self.telefonische_erreichbarkeit or {}).get(day_name, [])
            
            for slot in day_slots:
                start_time = slot.get("start", "")
                end_time = slot.get("end", "")
                
                if not start_time or not end_time:
                    continue
                    
                # Calculate duration in minutes
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = datetime.strptime(end_time, "%H:%M")
                duration_minutes = (end_dt - start_dt).total_seconds() / 60
                
                if duration_minutes >= min_duration_minutes:
                    return {
                        "date": check_date,
                        "day": day_name,
                        "start": start_time,
                        "end": end_time,
                        "duration_minutes": duration_minutes
                    }
                    
        return None
    
    def matches_patient_preferences(self, patient_data: Dict[str, Any]) -> bool:
        """Check if therapist preferences match patient characteristics.
        
        Args:
            patient_data: Dictionary with patient information
            
        Returns:
            Boolean indicating if therapist accepts this type of patient
        """
        # Check age preference
        if self.alter_min or self.alter_max:
            patient_age = patient_data.get('alter')
            if patient_age:
                if self.alter_min and patient_age < self.alter_min:
                    return False
                if self.alter_max and patient_age > self.alter_max:
                    return False
        
        # Check gender preference
        if self.geschlechtspraeferenz and self.geschlechtspraeferenz != "Egal":
            patient_gender = patient_data.get('geschlecht')
            if patient_gender and patient_gender != self.geschlechtspraeferenz:
                return False
        
        # Check diagnosis preference
        if self.bevorzugte_diagnosen:
            patient_diagnosis = patient_data.get('diagnose')
            if patient_diagnosis and patient_diagnosis not in self.bevorzugte_diagnosen:
                # This is a soft preference - we might still include them
                pass
        
        # Check group therapy preference
        if self.bevorzugt_gruppentherapie:
            if not patient_data.get('offen_fuer_gruppentherapie', False):
                # This is a soft preference
                pass
        
        return True