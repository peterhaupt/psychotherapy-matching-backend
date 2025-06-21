"""Matching algorithms package - Anfrage System."""
# Import all functions from the anfrage creator
from .anfrage_creator import (
    # Core functions
    get_eligible_patients_for_therapist,
    get_contactable_therapists,
    get_active_patient_searches,
    apply_hard_constraints,
    check_hard_constraints,
    select_anfrage_patients,
    
    # Constraint functions
    check_distance_constraint,
    check_exclusion_constraint,
    check_gender_preference,
    
    # Conflict resolution
    detect_conflicts,
    resolve_conflicts,
    
    # Analytics
    calculate_anfrage_efficiency,
    
    # Helper functions
    build_address,
    parse_time,
    calculate_age
)

__all__ = [
    # Core functions
    'get_eligible_patients_for_therapist',
    'get_contactable_therapists',
    'get_active_patient_searches',
    'apply_hard_constraints',
    'check_hard_constraints',
    'select_anfrage_patients',
    
    # Constraint functions
    'check_distance_constraint',
    'check_exclusion_constraint',
    'check_gender_preference',
    
    # Conflict resolution
    'detect_conflicts',
    'resolve_conflicts',
    
    # Analytics
    'calculate_anfrage_efficiency',
    
    # Helper functions
    'build_address',
    'parse_time',
    'calculate_age'
]