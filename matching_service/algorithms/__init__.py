"""Matching algorithms package - Bundle System."""
# Import all functions from the bundle creator
from .bundle_creator import (
    # Bundle creation functions
    create_bundles_for_all_therapists,
    create_bundle_for_therapist,
    get_eligible_patients_for_therapist,
    apply_hard_constraints,
    apply_progressive_filtering,
    select_bundle_patients,
    
    # Helper functions
    check_distance_constraint,
    check_exclusion_constraint,
    check_gender_preference,
    score_by_availability,
    score_by_therapist_preferences,
    
    # Conflict resolution
    detect_conflicts,
    resolve_conflicts,
    
    # Analytics
    calculate_bundle_efficiency,
    analyze_therapist_preferences
)

__all__ = [
    # Bundle creation functions
    'create_bundles_for_all_therapists',
    'create_bundle_for_therapist',
    'get_eligible_patients_for_therapist',
    'apply_hard_constraints',
    'apply_progressive_filtering',
    'select_bundle_patients',
    
    # Helper functions
    'check_distance_constraint',
    'check_exclusion_constraint',
    'check_gender_preference',
    'score_by_availability',
    'score_by_therapist_preferences',
    
    # Conflict resolution
    'detect_conflicts',
    'resolve_conflicts',
    
    # Analytics
    'calculate_bundle_efficiency',
    'analyze_therapist_preferences'
]