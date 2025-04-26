"""Patient database models."""
from datetime import date
from enum import Enum

from sqlalchemy import (
    Boolean, Column, Date, Enum as SQLAlchemyEnum,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB

from shared.utils.database import Base


class PatientStatus(str, Enum):
    """Enumeration for patient status values."""

    OPEN = "offen"
    SEARCHING = "auf der Suche"
    IN_THERAPY = "in Therapie"
    THERAPY_COMPLETED = "Therapie abgeschlossen"
    SEARCH_ABORTED = "Suche abgebrochen"
    THERAPY_ABORTED = "Therapie abgebrochen"


class TherapistGenderPreference(str, Enum):
    """Enumeration for therapist gender preferences."""

    MALE = "Männlich"
    FEMALE = "Weiblich"
    ANY = "Egal"


class Patient(Base):
    """Patient database model.

    This model represents a patient in the psychotherapy matching platform,
    including personal information, medical details, preferences, and
    therapy history.
    """

    __tablename__ = "patients"
    __table_args__ = {"schema": "patient_service"}

    id = Column(Integer, primary_key=True, index=True)

    # Personal Information
    anrede = Column(String(10))
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    strasse = Column(String(255))
    plz = Column(String(10))
    ort = Column(String(100))
    email = Column(String(255))
    telefon = Column(String(50))

    # Medical Information
    hausarzt = Column(String(255))
    krankenkasse = Column(String(100))
    krankenversicherungsnummer = Column(String(50))
    geburtsdatum = Column(Date)
    diagnose = Column(String(50))  # ICD-10 Diagnose

    # Process Status
    vertraege_unterschrieben = Column(Boolean, default=False)
    psychotherapeutische_sprechstunde = Column(Boolean, default=False)
    startdatum = Column(Date)  # Beginn der Platzsuche
    erster_therapieplatz_am = Column(Date)
    funktionierender_therapieplatz_am = Column(Date)
    status = Column(
        SQLAlchemyEnum(PatientStatus),
        default=PatientStatus.OPEN
    )
    empfehler_der_unterstuetzung = Column(Text)

    # Availability
    zeitliche_verfuegbarkeit = Column(JSONB)  # Wochentage und Uhrzeiten
    raeumliche_verfuegbarkeit = Column(JSONB)  # Maximale Entfernung/Fahrzeit
    verkehrsmittel = Column(String(50))  # Auto oder ÖPNV

    # Preferences
    offen_fuer_gruppentherapie = Column(Boolean, default=False)
    offen_fuer_diga = Column(Boolean, default=False)  # Digitale Anwendungen
    letzter_kontakt = Column(Date)

    # Medical History
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

    # Therapy Goals and Expectations
    anlass_fuer_die_therapiesuche = Column(Text)
    erwartungen_an_die_therapie = Column(Text)
    therapieziele = Column(Text)
    fruehere_therapieerfahrungen = Column(Text)

    # Therapist Exclusions and Preferences
    ausgeschlossene_therapeuten = Column(JSONB)  # Liste von Therapeuten-IDs
    bevorzugtes_therapeutengeschlecht = Column(
        SQLAlchemyEnum(TherapistGenderPreference),
        default=TherapistGenderPreference.ANY
    )

    # Timestamps
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)

    def __repr__(self):
        """Provide a string representation of the Patient instance."""
        return f"<Patient {self.vorname} {self.nachname}>"
