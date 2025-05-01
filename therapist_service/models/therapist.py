"""Therapist database models."""
from datetime import date
from enum import Enum

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
    and contact history.
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

    # Availability
    freie_einzeltherapieplaetze_ab = Column(Date)
    freie_gruppentherapieplaetze_ab = Column(Date)

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