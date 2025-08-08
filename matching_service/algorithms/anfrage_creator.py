"""Anfrage creation algorithm for the therapy matching platform.

This module implements the manual therapist selection and anfrage creation
with hard constraints only (no scoring or progressive filtering).

Updated with 8-tier email priority sorting for Phase 2 implementation.
FIXED: Hard constraints for therapy procedure, gender preference, and group therapy matching.
PHASE 3: Email deduplication to prevent multiple emails to same practice.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import re

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


def _normalize_for_email_check(name: str) -> str:
    """Normalize a name for email matching (handle umlauts).
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name with umlauts replaced
    """
    if not name:
        return ""
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Replace German umlauts
    umlaut_replacements = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'ß': 'ss'
    }
    
    for umlaut, replacement in umlaut_replacements.items():
        normalized = normalized.replace(umlaut, replacement)
    
    return normalized


def _identify_practice_owner(therapist_group: List[Dict[str, Any]], email: str) -> Dict[str, Any]:
    """Identify the practice owner from a group of therapists sharing the same email.
    
    Selection priority:
    1. Therapist whose last name appears in the email (with umlaut handling)
    2. Therapist with professional title (Dr., Prof.)
    3. Therapist with earliest creation date (lowest ID)
    
    Args:
        therapist_group: List of therapists with the same email
        email: The shared email address
        
    Returns:
        The identified practice owner
    """
    if len(therapist_group) == 1:
        return therapist_group[0]
    
    # Normalize email for comparison
    email_lower = email.lower() if email else ""
    
    # Priority 1: Check if last name appears in email
    for therapist in therapist_group:
        last_name = therapist.get('nachname', '')
        if last_name:
            normalized_name = _normalize_for_email_check(last_name)
            if normalized_name and normalized_name in email_lower:
                logger.debug(f"Selected therapist {therapist.get('id')} as practice owner - last name '{last_name}' found in email")
                return therapist
    
    # Priority 2: Check for professional titles
    title_priority = {'Prof.': 1, 'Prof': 1, 'Dr.': 2, 'Dr': 2}
    therapists_with_titles = []
    
    for therapist in therapist_group:
        title = therapist.get('titel', '')
        if title:
            # Check for any recognized title
            for title_key, priority in title_priority.items():
                if title_key in title:
                    therapists_with_titles.append((priority, therapist))
                    break
    
    if therapists_with_titles:
        # Sort by priority (lower number = higher priority)
        therapists_with_titles.sort(key=lambda x: x[0])
        selected = therapists_with_titles[0][1]
        logger.debug(f"Selected therapist {selected.get('id')} as practice owner - has title '{selected.get('titel')}'")
        return selected
    
    # Priority 3: Fallback to earliest created (lowest ID)
    therapist_group.sort(key=lambda t: t.get('id', float('inf')))
    selected = therapist_group[0]
    logger.debug(f"Selected therapist {selected.get('id')} as practice owner - earliest created")
    return selected


def get_therapists_for_selection(db: Session, plz_prefix: str) -> List[Dict[str, Any]]:
    """Get therapists for manual selection filtered by PLZ prefix with email deduplication.
    
    Phase 3 Implementation: Email deduplication to prevent multiple emails to same practice.
    Groups therapists by email and returns only practice owners.
    
    Args:
        db: Database session
        plz_prefix: Two-digit PLZ prefix (e.g., "52")
        
    Returns:
        List of practice owner therapists sorted by criteria
    """
    # Get all active therapists with PLZ prefix filter
    therapists = TherapistService.get_all_therapists(status='aktiv', plz_prefix=plz_prefix)
    
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
    
    # PHASE 3: Group therapists by email address
    email_groups = {}  # email -> list of therapists
    no_email_therapists = []  # therapists without email
    
    for therapist in therapists:
        email = therapist.get('email')
        if email:
            email = email.strip().lower()  # Normalize email for grouping
            if email not in email_groups:
                email_groups[email] = []
            email_groups[email].append(therapist)
        else:
            no_email_therapists.append(therapist)
    
    # Apply group-wide exclusions and identify practice owners
    filtered = []
    
    # Process email groups
    for email, group in email_groups.items():
        # Check if ANY therapist in the group has pending anfragen
        group_has_pending = any(t.get('id') in pending_therapist_ids for t in group)
        
        if group_has_pending:
            logger.debug(f"Skipping email group {email} - at least one therapist has pending anfragen")
            continue
        
        # Check if ANY therapist in the group is in cooling period
        group_in_cooling = False
        today = date.today()
        
        for therapist in group:
            next_contact = therapist.get('naechster_kontakt_moeglich')
            if next_contact and datetime.fromisoformat(next_contact).date() > today:
                group_in_cooling = True
                break
        
        if group_in_cooling:
            logger.debug(f"Skipping email group {email} - at least one therapist is in cooling period")
            continue
        
        # Identify and add the practice owner
        practice_owner = _identify_practice_owner(group, email)
        filtered.append(practice_owner)
        
        if len(group) > 1:
            logger.info(f"Selected therapist {practice_owner.get('id')} as practice owner for email {email} (group of {len(group)})")
    
    # Process therapists without email (not grouped)
    for therapist in no_email_therapists:
        # Skip if therapist has pending anfragen
        if therapist.get('id') in pending_therapist_ids:
            logger.debug(f"Skipping therapist {therapist.get('id')} - has pending anfragen")
            continue
        
        # Check if contactable today
        next_contact = therapist.get('naechster_kontakt_moeglich')
        # None means contactable
        if next_contact is None or datetime.fromisoformat(next_contact).date() <= date.today():
            filtered.append(therapist)
    
    # Sort according to business rules - EMAIL FIRST WITHIN EACH TIER
    def sort_key(t):
        is_available = t.get('potenziell_verfuegbar', False)
        is_informed = t.get('ueber_curavani_informiert', False)
        has_email = bool(t.get('email'))  # Check if therapist has email
        
        # Priority order with email preference:
        # 1. Available AND informed WITH email (return 0)
        # 2. Available AND not informed WITH email (return 1)
        # 3. Not available AND informed WITH email (return 2)
        # 4. Others WITH email (return 3)
        # 5. Available AND informed WITHOUT email (return 4)
        # 6. Available AND not informed WITHOUT email (return 5)
        # 7. Not available AND informed WITHOUT email (return 6)
        # 8. Others WITHOUT email (return 7)
        
        base_priority = 0
        if is_available and is_informed:
            base_priority = 0
        elif is_available and not is_informed:
            base_priority = 1
        elif not is_available and is_informed:
            base_priority = 2
        else:
            base_priority = 3
        
        # Add 4 to priority if no email (pushes to second tier)
        if not has_email:
            base_priority += 4
        
        return (base_priority, t.get('nachname', ''), t.get('vorname', ''))
    
    filtered.sort(key=sort_key)
    
    logger.info(f"Email deduplication: {len(therapists)} total therapists -> {len(filtered)} practice owners")
    
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
    # FIXED: Gender preference
    gender_pref = patient.get('bevorzugtes_therapeutengeschlecht')
    if gender_pref and gender_pref != 'Egal':
        therapist_gender = therapist.get('geschlecht')
        
        # Map therapist gender to preference format for comparison
        if therapist_gender == 'männlich':
            therapist_gender_mapped = 'Männlich'
        elif therapist_gender == 'weiblich':
            therapist_gender_mapped = 'Weiblich'
        else:
            # For 'divers' and 'keine_Angabe', they don't match specific preferences
            therapist_gender_mapped = therapist_gender
        
        if therapist_gender_mapped != gender_pref:
            logger.debug(f"Gender preference not met: patient wants {gender_pref}, therapist is {therapist_gender}")
            return False
    
    # FIXED: Therapy procedure preference (now single enum, not array)
    preferred_procedure = patient.get('bevorzugtes_therapieverfahren')
    if preferred_procedure and preferred_procedure != 'egal':
        therapist_procedure = therapist.get('psychotherapieverfahren')
        
        if therapist_procedure != preferred_procedure:
            logger.debug(f"Therapy procedure preference not met: patient wants {preferred_procedure}, therapist offers {therapist_procedure}")
            return False
    
    # Group therapy preference - patients can be sent to any therapist regardless of their preference
    # This constraint is only enforced from the therapist side (see check_therapist_preferences)
    
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
        patient_gender = patient.get('geschlecht')
        
        # Map patient gender to preference format for comparison
        if patient_gender == 'männlich':
            patient_gender_mapped = 'Männlich'
        elif patient_gender == 'weiblich':
            patient_gender_mapped = 'Weiblich'
        else:
            # For 'divers' and 'keine_Angabe', they don't match specific preferences
            patient_gender_mapped = patient_gender
        
        if patient_gender_mapped != gender_pref:
            logger.debug(f"Therapist gender preference not met: therapist wants {gender_pref}, patient is {patient_gender}")
            return False
    
    # FIXED: Group therapy preference (one-directional constraint)
    # If therapist prefers group therapy, only patients open to group therapy should be sent
    therapist_prefers_group = therapist.get('bevorzugt_gruppentherapie')
    if therapist_prefers_group is True:
        patient_open_to_group = patient.get('offen_fuer_gruppentherapie')
        if patient_open_to_group is not True:
            logger.debug(f"Therapist prefers group therapy but patient is not open to it")
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