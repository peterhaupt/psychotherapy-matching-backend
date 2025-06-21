"""Therapist database models with German enum consistency."""
from datetime import date
from enum import Enum

from sqlalchemy import (
    Boolean, Column, Date, Enum as SQLAlchemyEnum,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB

from shared.utils.database import Base


class TherapistStatus(str, Enum):
    """Enumeration for therapist status values - fully German."""

    aktiv = "aktiv"
    gesperrt = "gesperrt"
    inaktiv = "inaktiv"


class Therapist(Base):
    """Therapist database model.

    This model represents a therapist in the psychotherapy matching platform,
    including personal information, professional details, availability,
    inquiry preferences, and contact history.
    
    All field names use German terminology for consistency with the database
    schema and overall architecture.
    """

    __tablename__ = "therapeuten"
    __table_args__ = {"schema": "therapist_service"}

    id = Column(Integer, primary_key=True, index=True)

    # Personal Information (German field names)
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

    # Professional Information (German field names)
    kassensitz = Column(Boolean, default=True)
    geschlecht = Column(String(20))
    telefonische_erreichbarkeit = Column(JSONB)
    fremdsprachen = Column(JSONB)
    psychotherapieverfahren = Column(JSONB)
    zusatzqualifikationen = Column(Text)
    besondere_leistungsangebote = Column(Text)

    # Contact History (German field names)
    letzter_kontakt_email = Column(Date)
    letzter_kontakt_telefon = Column(Date)
    letztes_persoenliches_gespraech = Column(Date)

    # Availability (German field names)
    potenziell_verfuegbar = Column(Boolean, default=False)
    potenziell_verfuegbar_notizen = Column(Text)
    ueber_curavani_informiert = Column(Boolean, default=False)  # NEW: Whether therapist is informed about Curavani

    # Inquiry System Fields (German field names - renamed from Bundle)
    naechster_kontakt_moeglich = Column(Date)
    bevorzugte_diagnosen = Column(JSONB)
    alter_min = Column(Integer)
    alter_max = Column(Integer)
    geschlechtspraeferenz = Column(String(50))
    arbeitszeiten = Column(JSONB)
    bevorzugt_gruppentherapie = Column(Boolean, default=False)

    # Status Information (German field names)
    status = Column(
        SQLAlchemyEnum(TherapistStatus, name='therapeutstatus', native_enum=True),
        default=TherapistStatus.aktiv
    )
    sperrgrund = Column(Text)
    sperrdatum = Column(Date)

    # Timestamps (technical fields remain in English)
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)

    def __repr__(self):
        """Provide a string representation of the Therapist instance."""
        return f"<Therapist {self.titel or ''} {self.vorname} {self.nachname}>"