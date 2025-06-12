"""Bundle creation algorithm for the therapy matching platform.

This module implements the core bundle-based matching algorithm that creates
groups of 3-6 patients for each contactable therapist using progressive filtering.
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

from sqlalchemy.orm import Session

from models import Platzsuche, Therapeutenanfrage
from models.platzsuche import SuchStatus
from services import (
    PatientService, 
    TherapistService, 
    GeoCodingService,
    BundleService
)
from shared.config import get_config

# Get configuration and logger
config = get_config()
logger = logging.getLogger(__name__)

# Constants
MIN_BUNDLE_SIZE = 3
MAX_BUNDLE_SIZE = 6
DEFAULT_MAX_DISTANCE_KM = 50  # Default if patient doesn't specify


def create_bundles_for_all_therapists(db: Session) -> List[Therapeutenanfrage]:
    """Create bundles for all eligible therapists.
    
    Main entry point for the bundle creation algorithm. Creates optimal
    bundles of 3-6 patients for each contactable therapist.
    
    Args:
        db: Database session
        
    Returns:
        List of created Therapeutenanfrage (bundle) instances
    """
    logger.info("Starting bundle creation for all eligible therapists")
    
    # Step 1: Get contactable therapists
    therapists = get_contactable_therapists()
    logger.info(f"Found {len(therapists)} contactable therapists")
    
    if not therapists:
        logger.warning("No contactable therapists found")
        return []
    
    # Step 2: Get active patient searches
    patient_searches = get_active_patient_searches(db)
    logger.info(f"Found {len(patient_searches)} active patient searches")
    
    if not patient_searches:
        logger.warning("No active patient searches found")
        return []
    
    # Step 3: Create bundles for each therapist
    created_bundles = []
    
    for therapist in therapists:
        try:
            bundle = create_bundle_for_therapist(
                db,
                therapist,
                patient_searches
            )
            if bundle:
                created_bundles.append(bundle)
                logger.info(
                    f"Created bundle {bundle.id} for therapist {therapist['id']} "
                    f"with {bundle.buendelgroesse} patients"
                )
        except Exception as e:
            logger.error(
                f"Failed to create bundle for therapist {therapist['id']}: {str(e)}"
            )
            continue
    
    logger.info(f"Created {len(created_bundles)} bundles total")
    return created_bundles


def create_bundle_for_therapist(
    db: Session,
    therapist: Dict[str, Any],
    all_patient_searches: List[Platzsuche]
) -> Optional[Therapeutenanfrage]:
    """Create a bundle for a specific therapist.
    
    Args:
        db: Database session
        therapist: Therapist data dictionary
        all_patient_searches: List of all active patient searches
        
    Returns:
        Created Therapeutenanfrage instance or None if not enough patients
    """
    therapist_id = therapist['id']
    
    # Step 1: Apply hard constraints
    eligible_searches = apply_hard_constraints(
        therapist, 
        all_patient_searches
    )
    
    logger.debug(
        f"Therapist {therapist_id}: {len(eligible_searches)} patients "
        f"pass hard constraints"
    )
    
    if len(eligible_searches) < MIN_BUNDLE_SIZE:
        logger.debug(
            f"Therapist {therapist_id}: Not enough patients after hard constraints "
            f"({len(eligible_searches)} < {MIN_BUNDLE_SIZE})"
        )
        return None
    
    # Step 2: Apply progressive filtering
    filtered_searches = apply_progressive_filtering(
        therapist,
        eligible_searches
    )
    
    # Step 3: Select top patients by wait time
    bundle_patients = select_bundle_patients(
        filtered_searches,
        min_size=MIN_BUNDLE_SIZE,
        max_size=MAX_BUNDLE_SIZE
    )
    
    if len(bundle_patients) < MIN_BUNDLE_SIZE:
        logger.debug(
            f"Therapist {therapist_id}: Not enough patients for bundle "
            f"({len(bundle_patients)} < {MIN_BUNDLE_SIZE})"
        )
        return None
    
    # Step 4: Create the bundle
    patient_tuples = [(ps.id, ps.patient_id) for ps in bundle_patients]
    
    try:
        bundle = BundleService.create_bundle(
            db,
            therapist_id=therapist_id,
            patient_searches=patient_tuples
        )
        return bundle
    except Exception as e:
        logger.error(f"Failed to create bundle in database: {str(e)}")
        raise


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
    
    # Apply hard constraints
    eligible = apply_hard_constraints(therapist, all_searches)
    
    # Apply progressive filtering
    return apply_progressive_filtering(therapist, eligible)


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


def apply_progressive_filtering(
    therapist: Dict[str, Any],
    eligible_searches: List[Platzsuche]
) -> List[Platzsuche]:
    """Apply progressive filtering based on preferences.
    
    Applies filters in order of priority:
    1. Availability compatibility
    2. Therapist preferences (diagnosis, age, etc.)
    3. Sort by wait time
    
    Args:
        therapist: Therapist data
        eligible_searches: Patient searches that passed hard constraints
        
    Returns:
        Filtered and sorted list of patient searches
    """
    # Get patient data for all searches
    search_to_patient = {}
    for search in eligible_searches:
        patient = PatientService.get_patient(search.patient_id)
        if patient:
            search_to_patient[search.id] = patient
    
    # Calculate scores for each search
    scored_searches = []
    
    for search in eligible_searches:
        if search.id not in search_to_patient:
            continue
        
        patient = search_to_patient[search.id]
        score = calculate_patient_score(therapist, patient, search)
        scored_searches.append((search, score))
    
    # Sort by score (higher is better) and wait time (longer is better)
    scored_searches.sort(
        key=lambda x: (
            x[1],  # Score
            -x[0].created_at.timestamp()  # Negative timestamp (older = higher priority)
        ),
        reverse=True
    )
    
    return [search for search, _ in scored_searches]


def calculate_patient_score(
    therapist: Dict[str, Any],
    patient: Dict[str, Any],
    search: Platzsuche
) -> float:
    """Calculate a score for patient-therapist compatibility.
    
    Args:
        therapist: Therapist data
        patient: Patient data
        search: Patient search instance
        
    Returns:
        Compatibility score (0-100)
    """
    score = 0.0
    
    # 1. Availability compatibility (weight: 40)
    availability_score = score_by_availability(
        patient.get('zeitliche_verfuegbarkeit'),
        therapist.get('arbeitszeiten')
    )
    score += availability_score * 40
    
    # 2. Diagnosis preference (weight: 30)
    diagnosis_score = score_by_therapist_preferences(
        patient,
        therapist
    )
    score += diagnosis_score * 30
    
    # 3. Age preference (weight: 20)
    age_score = score_by_age_preference(
        patient.get('geburtsdatum'),
        therapist.get('alter_min'),
        therapist.get('alter_max')
    )
    score += age_score * 20
    
    # 4. Group therapy compatibility (weight: 10)
    group_score = score_by_group_therapy(
        patient.get('offen_fuer_gruppentherapie', False),
        therapist.get('bevorzugt_gruppentherapie', False)
    )
    score += group_score * 10
    
    return score


def score_by_availability(
    patient_availability: Optional[Dict],
    therapist_hours: Optional[Dict]
) -> float:
    """Score compatibility based on availability overlap.
    
    Args:
        patient_availability: Patient's availability schedule
        therapist_hours: Therapist's working hours
        
    Returns:
        Score between 0 and 1
    """
    if not patient_availability or not therapist_hours:
        return 0.5  # Neutral score if data missing
    
    # Calculate overlap hours
    total_overlap_hours = 0
    total_patient_hours = 0
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    for day in days:
        patient_slots = patient_availability.get(day, [])
        therapist_slots = therapist_hours.get(day, [])
        
        if not patient_slots or not therapist_slots:
            continue
        
        # Calculate overlap for this day
        for p_slot in patient_slots:
            p_start = parse_time(p_slot.get('start', '00:00'))
            p_end = parse_time(p_slot.get('end', '00:00'))
            p_hours = (p_end - p_start).total_seconds() / 3600
            total_patient_hours += p_hours
            
            for t_slot in therapist_slots:
                t_start = parse_time(t_slot.get('start', '00:00'))
                t_end = parse_time(t_slot.get('end', '00:00'))
                
                # Calculate overlap
                overlap_start = max(p_start, t_start)
                overlap_end = min(p_end, t_end)
                
                if overlap_start < overlap_end:
                    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
                    total_overlap_hours += overlap_hours
    
    if total_patient_hours == 0:
        return 0.5
    
    # Return ratio of overlap to patient availability
    return min(total_overlap_hours / total_patient_hours, 1.0)


def score_by_therapist_preferences(
    patient: Dict[str, Any],
    therapist: Dict[str, Any]
) -> float:
    """Score based on therapist's various preferences.
    
    Combines diagnosis preference and other factors.
    
    Args:
        patient: Patient data
        therapist: Therapist data
        
    Returns:
        Score between 0 and 1
    """
    total_score = 0.0
    weights = 0.0
    
    # Diagnosis preference (weight: 60%)
    patient_diagnosis = patient.get('diagnose')
    preferred_diagnoses = therapist.get('bevorzugte_diagnosen', [])
    
    if patient_diagnosis and preferred_diagnoses:
        diagnosis_score = score_by_diagnosis_preference(patient_diagnosis, preferred_diagnoses)
        total_score += diagnosis_score * 0.6
        weights += 0.6
    
    # Gender preference (weight: 40%)
    therapist_gender_pref = therapist.get('geschlechtspraeferenz')
    patient_gender = patient.get('geschlecht')
    
    if therapist_gender_pref and patient_gender:
        if therapist_gender_pref.lower() == 'egal' or not therapist_gender_pref:
            gender_score = 0.7
        elif therapist_gender_pref.upper() == patient_gender.upper():
            gender_score = 1.0
        else:
            gender_score = 0.3
        
        total_score += gender_score * 0.4
        weights += 0.4
    
    return total_score / weights if weights > 0 else 0.5


def score_by_diagnosis_preference(
    patient_diagnosis: Optional[str],
    preferred_diagnoses: List[str]
) -> float:
    """Score based on diagnosis preference match.
    
    Args:
        patient_diagnosis: Patient's ICD-10 diagnosis code
        preferred_diagnoses: List of therapist's preferred diagnoses
        
    Returns:
        Score between 0 and 1
    """
    if not patient_diagnosis or not preferred_diagnoses:
        return 0.5  # Neutral score
    
    # Exact match
    if patient_diagnosis in preferred_diagnoses:
        return 1.0
    
    # Category match (e.g., F32.1 matches F32)
    patient_category = patient_diagnosis.split('.')[0]
    for pref in preferred_diagnoses:
        if pref.split('.')[0] == patient_category:
            return 0.8
    
    return 0.3  # Low score for no match


def score_by_age_preference(
    patient_birthdate: Optional[str],
    min_age: Optional[int],
    max_age: Optional[int]
) -> float:
    """Score based on age preference match.
    
    Args:
        patient_birthdate: Patient's birthdate as string
        min_age: Therapist's minimum age preference
        max_age: Therapist's maximum age preference
        
    Returns:
        Score between 0 and 1
    """
    if not patient_birthdate:
        return 0.5  # Neutral if unknown
    
    try:
        birthdate = datetime.fromisoformat(patient_birthdate).date()
        age = calculate_age(birthdate)
    except:
        return 0.5  # Neutral if parsing fails
    
    # No preference
    if min_age is None and max_age is None:
        return 0.7  # Slightly positive
    
    # Check if within range
    if min_age and age < min_age:
        return 0.2  # Low score but not zero
    if max_age and age > max_age:
        return 0.2  # Low score but not zero
    
    return 1.0  # Perfect match


def score_by_group_therapy(
    patient_open: bool,
    therapist_prefers: bool
) -> float:
    """Score based on group therapy compatibility.
    
    Args:
        patient_open: Patient open for group therapy
        therapist_prefers: Therapist prefers group therapy
        
    Returns:
        Score between 0 and 1
    """
    if therapist_prefers and patient_open:
        return 1.0  # Perfect match
    elif therapist_prefers and not patient_open:
        return 0.2  # Mismatch
    elif not therapist_prefers and patient_open:
        return 0.7  # Patient flexible
    else:
        return 0.8  # Both prefer individual


def select_bundle_patients(
    filtered_searches: List[Platzsuche],
    min_size: int = MIN_BUNDLE_SIZE,
    max_size: int = MAX_BUNDLE_SIZE
) -> List[Platzsuche]:
    """Select patients for bundle based on filtering results.
    
    Args:
        filtered_searches: Pre-filtered and sorted patient searches
        min_size: Minimum bundle size
        max_size: Maximum bundle size
        
    Returns:
        Selected patient searches for the bundle
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
        
        # Get bundles for these therapists
        bundles = db.query(Therapeutenanfrage).filter(
            Therapeutenanfrage.therapist_id.in_(therapist_ids),
            Therapeutenanfrage.antwort_datum.isnot(None)
        ).order_by(Therapeutenanfrage.antwort_datum).all()
        
        if bundles:
            # First responder wins
            winning_therapist_id = bundles[0].therapist_id
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


# Analytics functions for future use

def calculate_bundle_efficiency(bundles: List[Therapeutenanfrage]) -> Dict[str, float]:
    """Calculate efficiency metrics for bundles.
    
    Args:
        bundles: List of bundles to analyze
        
    Returns:
        Dictionary of metrics
    """
    if not bundles:
        return {
            'average_acceptance_rate': 0.0,
            'average_bundle_size': 0.0,
            'response_rate': 0.0
        }
    
    total_accepted = sum(b.angenommen_anzahl for b in bundles)
    total_patients = sum(b.buendelgroesse for b in bundles)
    responded = sum(1 for b in bundles if b.antwort_datum is not None)
    
    return {
        'average_acceptance_rate': total_accepted / total_patients if total_patients > 0 else 0.0,
        'average_bundle_size': total_patients / len(bundles),
        'response_rate': responded / len(bundles)
    }


def analyze_therapist_preferences(
    therapist_id: int,
    historical_bundles: List[Therapeutenanfrage]
) -> Dict[str, Any]:
    """Analyze therapist's historical preferences from responses.
    
    Args:
        therapist_id: ID of the therapist
        historical_bundles: Past bundles for this therapist
        
    Returns:
        Dictionary of learned preferences
    """
    # This would analyze acceptance patterns to learn preferences
    # For now, return empty dict as placeholder
    return {
        'preferred_diagnoses': [],
        'preferred_age_range': None,
        'average_acceptance_rate': 0.0
    }