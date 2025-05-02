"""Matching algorithm implementation for the Matching Service."""
import logging
import requests
from typing import Dict, List, Optional, Any

from shared.utils.database import SessionLocal
from models.placement_request import PlacementRequest, PlacementRequestStatus

# Initialize logging
logger = logging.getLogger(__name__)

# Service URLs
PATIENT_SERVICE_URL = "http://patient-service:8001"
THERAPIST_SERVICE_URL = "http://therapist-service:8002"


def get_patient_data(patient_id: int) -> Optional[Dict[str, Any]]:
    """Get patient data from the Patient Service.

    Args:
        patient_id: ID of the patient

    Returns:
        Patient data or None if not found
    """
    try:
        response = requests.get(f"{PATIENT_SERVICE_URL}/api/patients/{patient_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error fetching patient data: {str(e)}")
        return None


def get_therapist_data(therapist_id: int) -> Optional[Dict[str, Any]]:
    """Get therapist data from the Therapist Service.

    Args:
        therapist_id: ID of the therapist

    Returns:
        Therapist data or None if not found
    """
    try:
        response = requests.get(f"{THERAPIST_SERVICE_URL}/api/therapists/{therapist_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error fetching therapist data: {str(e)}")
        return None


def get_all_therapists(
    status: Optional[str] = "ACTIVE"
) -> List[Dict[str, Any]]:
    """Get all therapists from the Therapist Service.

    Args:
        status: Optional status filter

    Returns:
        List of therapist data
    """
    try:
        params = {}
        if status:
            params['status'] = status
            
        response = requests.get(
            f"{THERAPIST_SERVICE_URL}/api/therapists",
            params=params
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        logger.error(f"Error fetching therapists: {str(e)}")
        return []


def find_matching_therapists(
    patient_id: int,
    max_distance: Optional[float] = None,
    gender_preference: Optional[str] = None,
    excluded_therapist_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """Find matching therapists for a patient based on criteria.
    
    Args:
        patient_id: ID of the patient seeking a therapist
        max_distance: Maximum distance in kilometers
        gender_preference: Optional gender preference
        excluded_therapist_ids: IDs of therapists to exclude
        
    Returns:
        List of matching therapists with distance information
    """
    # Get patient data
    patient = get_patient_data(patient_id)
    if not patient:
        logger.error(f"Patient {patient_id} not found")
        return []
    
    # Use patient preferences if not explicitly provided
    gender_preference = gender_preference or patient.get('bevorzugtes_therapeutengeschlecht')
    max_distance = max_distance or patient.get('raeumliche_verfuegbarkeit', {}).get('max_km')
    
    # Get list of excluded therapists
    excluded_ids = excluded_therapist_ids or []
    if patient.get('ausgeschlossene_therapeuten'):
        excluded_ids.extend(patient['ausgeschlossene_therapeuten'])
    
    # Get all active therapists
    therapists = get_all_therapists(status="ACTIVE")
    
    # Apply filters
    matches = []
    for therapist in therapists:
        # Skip excluded therapists
        if therapist['id'] in excluded_ids:
            continue
        
        # Apply gender filter if specified
        if gender_preference and gender_preference != "ANY":
            therapist_gender = therapist.get('geschlecht')
            if gender_preference == "MALE" and therapist_gender != "Männlich":
                continue
            if gender_preference == "FEMALE" and therapist_gender != "Weiblich":
                continue
        
        # Distance calculation would happen here
        # For now, we'll assume all therapists are within range
        # TODO: Implement geocoding service integration
        
        # Check if a placement request already exists
        db = SessionLocal()
        try:
            existing_request = db.query(PlacementRequest).filter(
                PlacementRequest.patient_id == patient_id,
                PlacementRequest.therapist_id == therapist['id'],
                PlacementRequest.status != PlacementRequestStatus.REJECTED
            ).first()
            
            if existing_request:
                # Skip if already matched
                continue
                
            # Add to matches
            matches.append({
                'therapist_id': therapist['id'],
                'therapist_name': f"{therapist.get('vorname')} {therapist.get('nachname')}",
                'therapist_data': therapist,
                # Placeholder for actual distance - would come from geocoding service
                'distance': 0
            })
            
        finally:
            db.close()
    
    # Sort by distance (would be more meaningful with actual distances)
    matches.sort(key=lambda x: x['distance'])
    
    return matches


def create_placement_requests(
    patient_id: int,
    therapist_ids: List[int],
    notes: Optional[str] = None
) -> List[int]:
    """Create placement requests for a patient and multiple therapists.
    
    Args:
        patient_id: ID of the patient
        therapist_ids: List of therapist IDs to match with
        notes: Optional notes for the requests
        
    Returns:
        List of created request IDs
    """
    request_ids = []
    db = SessionLocal()
    
    try:
        for therapist_id in therapist_ids:
            # Check if a request already exists
            existing = db.query(PlacementRequest).filter(
                PlacementRequest.patient_id == patient_id,
                PlacementRequest.therapist_id == therapist_id,
                PlacementRequest.status.in_([
                    PlacementRequestStatus.OPEN,
                    PlacementRequestStatus.IN_PROGRESS
                ])
            ).first()
            
            # Skip if already exists
            if existing:
                continue
                
            # Create new request
            request = PlacementRequest(
                patient_id=patient_id,
                therapist_id=therapist_id,
                status=PlacementRequestStatus.OPEN,
                notes=notes
            )
            
            db.add(request)
            db.flush()  # Get ID without committing
            
            request_ids.append(request.id)
        
        # Commit all changes
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating placement requests: {str(e)}")
    finally:
        db.close()
        
    return request_ids