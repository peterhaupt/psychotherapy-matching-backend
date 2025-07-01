"""Patient database models with full German consistency."""
from datetime import date
from enum import Enum

from sqlalchemy import (
    Boolean, Column, Date, Enum as SQLAlchemyEnum,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB

from shared.utils.database import Base


class Patientenstatus(str, Enum):
    """Enumeration for patient status values - fully German."""

    offen = "offen"
    auf_der_Suche = "auf_der_Suche"
    in_Therapie = "in_Therapie"
    Therapie_abgeschlossen = "Therapie_abgeschlossen"
    Suche_abgebrochen = "Suche_abgebrochen"
    Therapie_abgebrochen = "Therapie_abgebrochen"


class Therapeutgeschlechtspraeferenz(str, Enum):
    """Enumeration for therapist gender preferences - fully German."""

    Männlich = "Männlich"
    Weiblich = "Weiblich"
    Egal = "Egal"


class Therapieverfahren(str, Enum):
    """Enumeration for therapy procedures - fully German."""
    
    egal = "egal"
    Verhaltenstherapie = "Verhaltenstherapie"
    tiefenpsychologisch_fundierte_Psychotherapie = "tiefenpsychologisch_fundierte_Psychotherapie"


class Anrede(str, Enum):
    """Enumeration for salutation - fully German."""
    
    Herr = "Herr"
    Frau = "Frau"


class Geschlecht(str, Enum):
    """Enumeration for gender - fully German."""
    
    männlich = "männlich"
    weiblich = "weiblich"
    divers = "divers"
    keine_Angabe = "keine_Angabe"


class Patient(Base):
    """Patient database model.

    This model represents a patient in the psychotherapy matching platform,
    including personal information, medical details, preferences, and
    therapy history.
    
    All field names and enum values use German terminology for consistency
    with the database schema and overall architecture.
    """

    __tablename__ = "patienten"
    __table_args__ = {"schema": "patient_service"}

    id = Column(Integer, primary_key=True, index=True)

    # Personal Information (German field names)
    anrede = Column(
        SQLAlchemyEnum(Anrede, name='anrede', native_enum=True),
        nullable=False
    )
    geschlecht = Column(
        SQLAlchemyEnum(Geschlecht, name='geschlecht', native_enum=True),
        nullable=False
    )
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    strasse = Column(String(255))
    plz = Column(String(10))
    ort = Column(String(100))
    email = Column(String(255))
    telefon = Column(String(50))

    # Medical Information (German field names)
    hausarzt = Column(String(255))
    krankenkasse = Column(String(100))
    krankenversicherungsnummer = Column(String(50))
    geburtsdatum = Column(Date)
    diagnose = Column(String(50))  # ICD-10 Diagnose
    symptome = Column(Text)  # Symptoms description
    erfahrung_mit_psychotherapie = Column(Boolean)  # Experience with psychotherapy (changed from Text)
    letzte_sitzung_vorherige_psychotherapie = Column(Date)  # NEW: Last session of previous psychotherapy

    # Process Status (German field names)
    vertraege_unterschrieben = Column(Boolean, default=False)
    psychotherapeutische_sprechstunde = Column(Boolean, default=False)
    startdatum = Column(Date)  # Beginn der Platzsuche
    erster_therapieplatz_am = Column(Date)
    funktionierender_therapieplatz_am = Column(Date)
    status = Column(
        SQLAlchemyEnum(Patientenstatus, name='patientenstatus', native_enum=True),
        default=Patientenstatus.offen
    )
    empfehler_der_unterstuetzung = Column(Text)

    # Availability (German field names)
    zeitliche_verfuegbarkeit = Column(JSONB)  # Wochentage und Uhrzeiten
    raeumliche_verfuegbarkeit = Column(JSONB)  # Maximale Entfernung/Fahrzeit
    verkehrsmittel = Column(String(50))  # Auto oder ÖPNV

    # Preferences (German field names)
    offen_fuer_gruppentherapie = Column(Boolean, default=False)
    offen_fuer_diga = Column(Boolean, default=False)  # Digitale Anwendungen
    letzter_kontakt = Column(Date)

    # Therapist Exclusions and Preferences (German field names)
    ausgeschlossene_therapeuten = Column(JSONB)  # Liste von Therapeuten-IDs
    bevorzugtes_therapeutengeschlecht = Column(
        SQLAlchemyEnum(Therapeutgeschlechtspraeferenz, name='therapeutgeschlechtspraeferenz', native_enum=True),
        default=Therapeutgeschlechtspraeferenz.Egal
    )
    bevorzugtes_therapieverfahren = Column(
        SQLAlchemyEnum(Therapieverfahren, name='therapieverfahren', native_enum=True),
        default=Therapieverfahren.egal
    )  # Changed from ARRAY to single ENUM

    # Timestamps (technical fields remain in English)
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)

    def __repr__(self):
        """Provide a string representation of the Patient instance."""
        return f"<Patient {self.vorname} {self.nachname}>"