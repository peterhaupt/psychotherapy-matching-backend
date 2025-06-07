"""Matching algorithm implementation for the Matching Service - STUB."""
import logging
from typing import Dict, List, Optional, Any

from shared.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Service URLs from configuration
PATIENT_SERVICE_URL = config.get_service_url("patient", internal=True)
THERAPIST_SERVICE_URL = config.get_service_url("therapist", internal=True)
GEOCODING_SERVICE_URL = config.get_service_url("geocoding", internal=True)


# Stub functions - to be implemented with bundle system
def find_matching_therapists(patient_id: int) -> List[Dict[str, Any]]:
    """Find matching therapists for a patient - STUB.
    
    Args:
        patient_id: ID of the patient to match
        
    Returns:
        List of matching therapist data
    """
    logger.warning("find_matching_therapists is a stub - bundle system not yet implemented")
    return []


def create_placement_requests(patient_id: int, therapist_ids: List[int], notes: str = None) -> List[int]:
    """Create placement requests - STUB.
    
    Args:
        patient_id: ID of the patient
        therapist_ids: List of therapist IDs
        notes: Optional notes
        
    Returns:
        List of created request IDs
    """
    logger.warning("create_placement_requests is a stub - bundle system not yet implemented")
    return []


def get_patient_data(patient_id: int) -> Optional[Dict[str, Any]]:
    """Get patient data from patient service - STUB.
    
    Args:
        patient_id: ID of the patient
        
    Returns:
        Patient data dictionary or None
    """
    logger.warning("get_patient_data is a stub - implement with service call")
    return None


def get_therapist_data(therapist_id: int) -> Optional[Dict[str, Any]]:
    """Get therapist data from therapist service - STUB.
    
    Args:
        therapist_id: ID of the therapist
        
    Returns:
        Therapist data dictionary or None
    """
    logger.warning("get_therapist_data is a stub - implement with service call")
    return None


def get_all_therapists() -> List[Dict[str, Any]]:
    """Get all therapists from therapist service - STUB.
    
    Returns:
        List of all therapist data
    """
    logger.warning("get_all_therapists is a stub - implement with service call")
    return []