"""Anfrage creation algorithm for the therapy matching platform.

This module implements the manual therapist selection and anfrage creation
with hard constraints only (no scoring or progressive filtering).
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
from models.platzsuche import SuchStatus
from services import (
    PatientService, 
    TherapistService, 
    GeoCodingService
)
from shared.config import get_config

# Get configuration and logger
config = get_config()
logger = logging.getLogger(__name__)

# Get anfrage configuration
anfrage_config = config.get_anfrage_config()
MIN_ANFRAGE_SIZE = anfrage_config['min_size']  # 1
MAX_ANFRAGE_SIZE = anfrage_config['max_size']  # 6
PLZ_MATCH_DIGITS = anfrage_config['plz_match_digits']  # 2
DEFAULT_MAX_DISTANCE_KM = anfrage_config['default_max_distance_km']  # 25


def get_therapists_for_selection(db: Session, plz_prefix: str) -> List[Dict[str, Any]]:
    """Get therapists for manual selection filtered by PLZ prefix and pending anfragen.
    
    Args:
        db: Database session
        plz_prefix: Two-digit PLZ prefix (e.g., "52")
        
    Returns:
        List of therapist data dictionaries sorted by criteria
    """
    # Get all active therapists
    therapists = TherapistService.get_all_therapists(status='aktiv')
    
    # Get all therapist IDs with pending anfragen
    pending_therapist_ids = set()
    
    # Query for therapists with unsent anfragen
    unsent_anfragen = db.query(Therapeutenanfrage.therapist_id).filter(
        Therapeutenanfrage.gesendet_datum.is_(None)
    ).distinct().all()
    
    # Query for therapists with sent but unanswered anfragen
    unanswered_anfragen = db.query(Therapeutenanfrage.therapist_id).filter(
        and_(
            Therapeutenanfrage.gesendet_datum.isnot(None),
            Therapeutenanfrage.antwort_datum.is_(None)
        )
    ).distinct().all()
    
    # Combine the results
    for row in unsent_anfragen:
        pending_therapist_ids.add(row[0])
    for row in unanswered_anfragen:
        pending_therapist_ids.add(row[0])
    
    # Filter therapists
    filtered = []
    for therapist in therapists:
        # Skip if therapist has pending anfragen
        if therapist.get('id') in pending_therapist_ids:
            logger.debug(f"Skipping therapist {therapist.get('id')} - has pending anfragen")
            continue
            
        # Safe PLZ comparison with None handling
        therapist_plz = therapist.get('plz') or ''
        if therapist_plz.startswith(plz_prefix):
            # Check if contactable today
            next_contact = therapist.get('naechster_kontakt_moeglich')
            # None means contactable
            if next_contact is None or datetime.fromisoformat(next_contact).date() <= date.today():
                filtered.append(therapist)
    
    # Sort according to business rules
    def sort_key(t):
        is_available = t.get('potenziell_verfuegbar', False)
        is_informed = t.get('ueber_curavani_informiert', False)
        
        # Priority order:
        # 1. Available AND informed (return 0)
        # 2. Available AND not informed (return 1)
        # 3. Not available AND informed (return 2)
        # 4. Others (return 3)
        if is_available and is_informed:
            return (0, t.get('nachname', ''), t.get('vorname', ''))
        elif is_available and not is_informed:
            return (1, t.get('nachname', ''), t.get('vorname', ''))
        elif not is_available and is_informed:
            return (2, t.get('nachname', ''), t.get('vorname', ''))
        else:
            return (3, t.get('nachname', ''), t.get('vorname', ''))
    
    filtered.sort(key=sort_key)
    return filtered


def create_anfrage_for_therapist(
    db: Session,
    therapist_id: int,
    plz_prefix: str
) -> Optional[Therapeutenanfrage]:
    """Create anfrage for manually selected therapist.
    
    Args:
        db: Database session
        therapist_id: ID of the selected therapist
        plz_prefix: PLZ prefix for patient filtering
        
    Returns:
        Created Therapeutenanfrage or None if no matching patients
    """
    # Get therapist data
    therapist = TherapistService.get_therapist(therapist_id)
    if not therapist:
        logger.error(f"Therapist {therapist_id} not found")
        return None
    
    # Get active patient searches with matching PLZ
    patient_searches = db.query(Platzsuche).filter(
        Platzsuche.status == SuchStatus.aktiv
    ).order_by(Platzsuche.created_at).all()  # Oldest first
    
    # Filter by PLZ prefix
    matching_searches = []
    for search in patient_searches:
        patient = PatientService.get_patient(search.patient_id)
        if patient and (patient.get('plz') or '').startswith(plz_prefix):
            matching_searches.append((search, patient))
    
    # Apply hard constraints and collect eligible patients
    eligible_patients = []
    for search, patient in matching_searches:
        if check_all_hard_constraints(therapist, patient, search):
            eligible_patients.append((search.id, patient['id']))
    
    # If no eligible patients, return None
    if not eligible_patients:
        logger.info(f"No eligible patients found for therapist {therapist_id}")
        return None
    
    # Take up to MAX_ANFRAGE_SIZE patients
    selected_patients = eligible_patients[:MAX_ANFRAGE_SIZE]
    
    # Create the anfrage
    from services import AnfrageService
    anfrage = AnfrageService.create_anfrage(db, therapist_id, selected_patients)
    
    logger.info(
        f"Created anfrage {anfrage.id} for therapist {therapist_id} "
        f"with {len(selected_patients)} patients"
    )
    
    return anfrage


def check_all_hard_constraints(
    therapist: Dict[str, Any],
    patient: Dict[str, Any],
    search: Platzsuche
) -> bool:
    """Check if all hard constraints are satisfied.
    
    Args:
        therapist: Therapist data
        patient: Patient data
        search: Patient search instance
        
    Returns:
        True if all hard constraints pass, False otherwise
    """
    # 1. Distance check
    if not check_distance_constraint(patient, therapist):
        return False
    
    # 2. Exclusion check
    if not check_exclusion_constraint(search, therapist['id']):
        return False
    
    # 3. Patient preferences (ALL must be satisfied or null)
    if not check_patient_preferences(therapist, patient):
        return False
    
    # 4. Therapist preferences (ALL must be satisfied or null)
    if not check_therapist_preferences(therapist, patient):
        return False
    
    return True


def check_distance_constraint(
    patient: Dict[str, Any],
    therapist: Dict[str, Any]
) -> bool:
    """Check if therapist is within patient's travel distance.
    
    Args:
        patient: Patient data with address and max_travel_distance
        therapist: Therapist data with address
        
    Returns:
        True if within distance, False otherwise
    """
    # Get max travel distance with None handling
    max_distance = (patient.get('raeumliche_verfuegbarkeit') or {}).get(
        'max_km', 
        DEFAULT_MAX_DISTANCE_KM
    )
    
    # Build addresses
    patient_address = build_address(patient)
    therapist_address = build_address(therapist)
    
    if not patient_address or not therapist_address:
        logger.warning(
            f"Missing address for distance calculation: "
            f"patient={patient_address}, therapist={therapist_address}"
        )
        return True  # Allow if we can't calculate
    
    # Calculate distance with None handling
    travel_mode = (patient.get('verkehrsmittel') or 'car').lower()
    if travel_mode == 'öpnv':
        travel_mode = 'transit'
    elif travel_mode not in ['car', 'transit']:
        travel_mode = 'car'
    
    distance = GeoCodingService.calculate_distance(
        patient_address,
        therapist_address,
        travel_mode
    )
    
    if distance is None:
        logger.warning(
            f"Could not calculate distance between {patient_address} "
            f"and {therapist_address}"
        )
        return True  # Allow if calculation fails
    
    return distance <= max_distance


def check_exclusion_constraint(
    search: Platzsuche,
    therapist_id: int
) -> bool:
    """Check if therapist is not excluded by patient.
    
    Args:
        search: Patient search instance
        therapist_id: ID of the therapist
        
    Returns:
        True if not excluded, False if excluded
    """
    return not search.is_therapist_excluded(therapist_id)


def check_patient_preferences(
    therapist: Dict[str, Any],
    patient: Dict[str, Any]
) -> bool:
    """Check if therapist satisfies all patient preferences.
    
    All preferences must be satisfied if specified (not null/Egal).
    
    Args:
        therapist: Therapist data
        patient: Patient data
        
    Returns:
        True if all preferences satisfied or not specified
    """
    # Gender preference
    gender_pref = patient.get('bevorzugtes_therapeutengeschlecht')
    if gender_pref and gender_pref != 'Egal':
        therapist_gender = (therapist.get('geschlecht') or '').lower()
        # Map therapist gender to preference format
        if therapist_gender in ['m', 'männlich', 'mann']:
            therapist_gender = 'Männlich'
        elif therapist_gender in ['f', 'w', 'weiblich', 'frau']:
            therapist_gender = 'Weiblich'
        
        if therapist_gender != gender_pref:
            logger.debug(f"Gender preference not met: wanted {gender_pref}, got {therapist_gender}")
            return False
    
    # REMOVED: Age preference check for therapist age
    
    # Therapy procedure preference
    preferred_procedures = patient.get('bevorzugtes_therapieverfahren') or []
    if preferred_procedures and 'egal' not in preferred_procedures:
        therapist_procedures = therapist.get('psychotherapieverfahren') or []
        # Check if at least one preferred procedure matches
        if not any(proc in therapist_procedures for proc in preferred_procedures):
            logger.debug(f"No matching therapy procedures")
            return False
    
    # Group therapy preference - None treated as False
    if patient.get('offen_fuer_gruppentherapie', False) is False:
        if therapist.get('bevorzugt_gruppentherapie') is True:
            logger.debug("Patient not open for group therapy but therapist prefers it")
            return False
    
    return True


def check_therapist_preferences(
    therapist: Dict[str, Any],
    patient: Dict[str, Any]
) -> bool:
    """Check if patient satisfies all therapist preferences.
    
    All preferences must be satisfied if specified.
    
    Args:
        therapist: Therapist data
        patient: Patient data
        
    Returns:
        True if all preferences satisfied or not specified
    """
    # Diagnosis preference
    preferred_diagnoses = therapist.get('bevorzugte_diagnosen') or []
    if preferred_diagnoses:
        patient_diagnosis = patient.get('diagnose')
        if patient_diagnosis not in preferred_diagnoses:
            logger.debug(f"Patient diagnosis {patient_diagnosis} not in preferred list")
            return False
    
    # Age preference (PATIENT age, not therapist age - this stays)
    min_age = therapist.get('alter_min')
    max_age = therapist.get('alter_max')
    
    # FIXED: Treat 0 as None (no preference) since no therapist wants 0-year-old patients
    if min_age == 0:
        min_age = None
    if max_age == 0:
        max_age = None
    
    if min_age is not None or max_age is not None:
        patient_birthdate = patient.get('geburtsdatum')
        if patient_birthdate:
            try:
                patient_age = calculate_age(datetime.fromisoformat(patient_birthdate).date())
                if min_age is not None and patient_age < min_age:
                    logger.debug(f"Patient too young: {patient_age} < {min_age}")
                    return False
                if max_age is not None and patient_age > max_age:
                    logger.debug(f"Patient too old: {patient_age} > {max_age}")
                    return False
            except (ValueError, TypeError):
                logger.debug("Cannot verify age preference - invalid patient birthdate")
                return False
        else:
            logger.debug("Cannot verify age preference - patient birthdate missing")
            return False
    
    # Gender preference
    gender_pref = therapist.get('geschlechtspraeferenz')
    if gender_pref and gender_pref != 'Egal':
        patient_gender = (patient.get('geschlecht') or '').lower()
        # Normalize gender values
        if patient_gender in ['m', 'männlich', 'mann']:
            patient_gender = 'Männlich'
        elif patient_gender in ['f', 'w', 'weiblich', 'frau']:
            patient_gender = 'Weiblich'
        
        if patient_gender != gender_pref:
            logger.debug(f"Therapist gender preference not met: wanted {gender_pref}, got {patient_gender}")
            return False
    
    return True


# Helper functions

def build_address(entity: Dict[str, Any]) -> Optional[str]:
    """Build address string from entity data.
    
    Args:
        entity: Patient or therapist data
        
    Returns:
        Address string or None if incomplete
    """
    street = (entity.get('strasse') or '').strip()
    postal = (entity.get('plz') or '').strip()
    city = (entity.get('ort') or '').strip()
    
    if not city:  # Minimum requirement
        return None
    
    parts = []
    if street:
        parts.append(street)
    if postal:
        parts.append(postal)
    parts.append(city)
    
    return ', '.join(parts)


def calculate_age(birthdate: date) -> int:
    """Calculate age from birthdate.
    
    Args:
        birthdate: Date of birth
        
    Returns:
        Age in years
    """
    if birthdate is None:
        raise ValueError("Birthdate cannot be None")
        
    today = date.today()
    age = today.year - birthdate.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    
    return age


# Analytics functions (kept for compatibility)

def calculate_anfrage_efficiency(anfragen: List[Therapeutenanfrage]) -> Dict[str, float]:
    """Calculate efficiency metrics for anfragen.
    
    Args:
        anfragen: List of anfragen to analyze
        
    Returns:
        Dictionary of metrics
    """
    if not anfragen:
        return {
            'average_acceptance_rate': 0.0,
            'average_anfrage_size': 0.0,
            'response_rate': 0.0
        }
    
    total_accepted = sum(a.angenommen_anzahl for a in anfragen)
    total_patients = sum(a.anfragegroesse for a in anfragen)
    responded = sum(1 for a in anfragen if a.antwort_datum is not None)
    
    return {
        'average_acceptance_rate': total_accepted / total_patients if total_patients > 0 else 0.0,
        'average_anfrage_size': total_patients / len(anfragen),
        'response_rate': responded / len(anfragen)
    }