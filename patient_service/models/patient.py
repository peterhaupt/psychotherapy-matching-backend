"""Patient database models with full German consistency."""
from datetime import date
from enum import Enum

from sqlalchemy import (
    Boolean, Column, Date, Enum as SQLAlchemyEnum,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from shared.utils.database import Base


class PatientStatus(str, Enum):
    """Enumeration for patient status values - fully German."""

    offen = "offen"
    auf_der_Suche = "auf_der_Suche"
    in_Therapie = "in_Therapie"
    Therapie_abgeschlossen = "Therapie_abgeschlossen"
    Suche_abgebrochen = "Suche_abgebrochen"
    Therapie_abgebrochen = "Therapie_abgebrochen"


class TherapistGenderPreference(str, Enum):
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
    symptome = Column(Text)  # NEW: Symptoms description
    erfahrung_mit_psychotherapie = Column(Text)  # NEW: Experience with psychotherapy

    # Process Status (German field names)
    vertraege_unterschrieben = Column(Boolean, default=False)
    psychotherapeutische_sprechstunde = Column(Boolean, default=False)
    startdatum = Column(Date)  # Beginn der Platzsuche
    erster_therapieplatz_am = Column(Date)
    funktionierender_therapieplatz_am = Column(Date)
    status = Column(
        SQLAlchemyEnum(PatientStatus, name='patientenstatus', native_enum=True),
        default=PatientStatus.offen
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

    # Medical History (German field names)
    psychotherapieerfahrung = Column(Boolean, default=False)
    stationaere_behandlung = Column(Boolean, default=False)
    berufliche_situation = Column(Text)
    familienstand = Column(String(50))
    aktuelle_psychische_beschwerden = Column(Text)
    beschwerden_seit = Column(Date)
    bisherige_behandlungen = Column(Text)
    relevante_koerperliche_erkrankungen = Column(Text)
    aktuelle_medikation = Column(Text)
    aktuelle_belastungsfaktoren = Column(Text)
    unterstuetzungssysteme = Column(Text)

    # Therapy Goals and Expectations (German field names)
    anlass_fuer_die_therapiesuche = Column(Text)
    erwartungen_an_die_therapie = Column(Text)
    therapieziele = Column(Text)
    fruehere_therapieerfahrungen = Column(Text)

    # Therapist Exclusions and Preferences (German field names)
    ausgeschlossene_therapeuten = Column(JSONB)  # Liste von Therapeuten-IDs
    bevorzugtes_therapeutengeschlecht = Column(
        SQLAlchemyEnum(TherapistGenderPreference, name='therapeutgeschlechtspraeferenz', native_enum=True),
        default=TherapistGenderPreference.Egal
    )
    bevorzugtes_therapieverfahren = Column(ARRAY(SQLAlchemyEnum(Therapieverfahren, name='therapieverfahren', native_enum=True)))  # NEW: PostgreSQL Array
    # REMOVED: bevorzugtes_therapeutenalter_min and bevorzugtes_therapeutenalter_max

    # Timestamps (technical fields remain in English)
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)

    def __repr__(self):
        """Provide a string representation of the Patient instance."""
        return f"<Patient {self.vorname} {self.nachname}>"