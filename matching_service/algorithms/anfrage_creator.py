"""Anfrage creation algorithm for the therapy matching platform.

This module implements the core anfrage-based matching algorithm that creates
groups of 1-6 patients for each manually selected therapist using hard constraints only.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict

from sqlalchemy.orm import Session

from models import Platzsuche, Therapeutenanfrage
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
DEFAULT_MAX_DISTANCE_KM = 50  # Default if patient doesn't specify


def get_eligible_patients_for_therapist(
    db: Session,
    therapist_id: int
) -> List[Platzsuche]:
    """Get all eligible patients for a specific therapist.
    
    Args:
        db: Database session
        therapist_id: ID of the therapist
        
    Returns:
        List of eligible patient searches
    """
    # Get therapist data
    therapist = TherapistService.get_therapist(therapist_id)
    if not therapist:
        logger.warning(f"Therapist {therapist_id} not found")
        return []
    
    # Get all active searches
    all_searches = get_active_patient_searches(db)
    
    # Apply hard constraints only
    return apply_hard_constraints(therapist, all_searches)


def get_contactable_therapists() -> List[Dict[str, Any]]:
    """Get all therapists who can be contacted (not in cooling period).
    
    Returns:
        List of therapist data dictionaries
    """
    return TherapistService.get_contactable_therapists()


def get_active_patient_searches(db: Session) -> List[Platzsuche]:
    """Get all active patient searches from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of active Platzsuche instances
    """
    return db.query(Platzsuche).filter(
        Platzsuche.status == SuchStatus.aktiv
    ).all()


def apply_hard_constraints(
    therapist: Dict[str, Any],
    patient_searches: List[Platzsuche]
) -> List[Platzsuche]:
    """Apply hard constraints that MUST be satisfied.
    
    Hard constraints:
    1. Distance constraint - patient within travel distance
    2. Exclusion constraint - therapist not excluded by patient
    3. Gender preference - therapist gender matches patient preference
    
    Args:
        therapist: Therapist data dictionary
        patient_searches: List of patient searches to filter
        
    Returns:
        List of patient searches that pass all hard constraints
    """
    eligible = []
    
    for search in patient_searches:
        # Get patient data
        patient = PatientService.get_patient(search.patient_id)
        if not patient:
            logger.warning(f"Could not fetch patient {search.patient_id}")
            continue
        
        # Check all hard constraints
        if not check_hard_constraints(therapist, patient, search):
            continue
        
        eligible.append(search)
    
    return eligible


def check_hard_constraints(
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
    # 1. Exclusion check
    if not check_exclusion_constraint(search, therapist['id']):
        logger.debug(
            f"Patient {patient['id']} has excluded therapist {therapist['id']}"
        )
        return False
    
    # 2. Gender preference check
    if not check_gender_preference(therapist, patient):
        logger.debug(
            f"Therapist {therapist['id']} gender doesn't match "
            f"patient {patient['id']} preference"
        )
        return False
    
    # 3. Distance check
    if not check_distance_constraint(patient, therapist):
        logger.debug(
            f"Therapist {therapist['id']} too far for patient {patient['id']}"
        )
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
    # Get max travel distance
    max_distance = patient.get('raeumliche_verfuegbarkeit', {}).get(
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
    
    # Calculate distance
    travel_mode = patient.get('verkehrsmittel', 'car').lower()
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


def check_gender_preference(
    therapist: Dict[str, Any],
    patient: Dict[str, Any]
) -> bool:
    """Check if therapist gender matches patient preference.
    
    Args:
        therapist: Therapist data
        patient: Patient data
        
    Returns:
        True if gender matches preference or no preference
    """
    preference = patient.get('bevorzugtes_therapeutengeschlecht', 'Egal')
    
    if preference == 'Egal' or not preference:
        return True
    
    therapist_gender = therapist.get('geschlecht', '').lower()
    
    # Map therapist gender to preference format
    if therapist_gender in ['m', 'männlich', 'mann']:
        therapist_gender = 'Männlich'
    elif therapist_gender in ['f', 'w', 'weiblich', 'frau']:
        therapist_gender = 'Weiblich'
    
    return therapist_gender == preference


def select_anfrage_patients(
    filtered_searches: List[Platzsuche],
    min_size: int = MIN_ANFRAGE_SIZE,
    max_size: int = MAX_ANFRAGE_SIZE
) -> List[Platzsuche]:
    """Select patients for anfrage based on filtering results.
    
    Args:
        filtered_searches: Pre-filtered patient searches
        min_size: Minimum anfrage size
        max_size: Maximum anfrage size
        
    Returns:
        Selected patient searches for the anfrage
    """
    # Simply take the top patients up to max_size
    return filtered_searches[:max_size]


def detect_conflicts(
    new_acceptances: List[Tuple[int, int]]
) -> List[Dict[str, Any]]:
    """Detect patients accepted by multiple therapists.
    
    Args:
        new_acceptances: List of tuples (patient_id, therapist_id)
        
    Returns:
        List of conflict dictionaries
    """
    # Track patient acceptances
    patient_therapists = defaultdict(list)
    
    for patient_id, therapist_id in new_acceptances:
        patient_therapists[patient_id].append(therapist_id)
    
    # Find conflicts
    conflicts = []
    for patient_id, therapist_ids in patient_therapists.items():
        if len(therapist_ids) > 1:
            conflicts.append({
                'patient_id': patient_id,
                'therapist_ids': therapist_ids,
                'conflict_count': len(therapist_ids)
            })
    
    return conflicts


def resolve_conflicts(
    db: Session,
    conflicts: List[Dict[str, Any]]
) -> Dict[int, int]:
    """Resolve conflicts when patient accepted by multiple therapists.
    
    First therapist to respond gets the patient.
    
    Args:
        db: Database session
        conflicts: List of conflict dictionaries
        
    Returns:
        Dictionary mapping patient_id to winning therapist_id
    """
    resolutions = {}
    
    for conflict in conflicts:
        patient_id = conflict['patient_id']
        therapist_ids = conflict['therapist_ids']
        
        # Get anfragen for these therapists
        anfragen = db.query(Therapeutenanfrage).filter(
            Therapeutenanfrage.therapist_id.in_(therapist_ids),
            Therapeutenanfrage.antwort_datum.isnot(None)
        ).order_by(Therapeutenanfrage.antwort_datum).all()
        
        if anfragen:
            # First responder wins
            winning_therapist_id = anfragen[0].therapist_id
            resolutions[patient_id] = winning_therapist_id
            
            logger.info(
                f"Resolved conflict for patient {patient_id}: "
                f"therapist {winning_therapist_id} wins"
            )
    
    return resolutions


# Helper functions

def build_address(entity: Dict[str, Any]) -> Optional[str]:
    """Build address string from entity data.
    
    Args:
        entity: Patient or therapist data
        
    Returns:
        Address string or None if incomplete
    """
    street = entity.get('strasse', '').strip()
    postal = entity.get('plz', '').strip()
    city = entity.get('ort', '').strip()
    
    if not city:  # Minimum requirement
        return None
    
    parts = []
    if street:
        parts.append(street)
    if postal:
        parts.append(postal)
    parts.append(city)
    
    return ', '.join(parts)


def parse_time(time_str: str) -> datetime:
    """Parse time string to datetime object.
    
    Args:
        time_str: Time in HH:MM format
        
    Returns:
        datetime object with today's date
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    except:
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def calculate_age(birthdate: date) -> int:
    """Calculate age from birthdate.
    
    Args:
        birthdate: Date of birth
        
    Returns:
        Age in years
    """
    today = date.today()
    age = today.year - birthdate.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    
    return age


# Analytics functions

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