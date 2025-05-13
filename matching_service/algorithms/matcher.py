"""Matching algorithm implementation for the Matching Service."""
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple

from shared.utils.database import SessionLocal
from models.placement_request import PlacementRequest, PlacementRequestStatus

# Initialize logging
logger = logging.getLogger(__name__)

# Service URLs
PATIENT_SERVICE_URL = "http://patient-service:8001"
THERAPIST_SERVICE_URL = "http://therapist-service:8002"
GEOCODING_SERVICE_URL = "http://geocoding-service:8005"


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


def calculate_distance(
    origin: Tuple[float, float] or str,
    destination: Tuple[float, float] or str,
    travel_mode: str = "car"
) -> Dict[str, Any]:
    """Calculate distance between two points using the Geocoding Service.
    
    Args:
        origin: Origin coordinates (lat, lon) or address
        destination: Destination coordinates (lat, lon) or address
        travel_mode: Mode of transport (car or transit)
        
    Returns:
        Dict with distance information
    """
    params = {}
    
    # Process origin
    if isinstance(origin, tuple):
        params['origin_lat'] = origin[0]
        params['origin_lon'] = origin[1]
    else:
        params['origin'] = origin
        
    # Process destination
    if isinstance(destination, tuple):
        params['destination_lat'] = destination[0]
        params['destination_lon'] = destination[1]
    else:
        params['destination'] = destination
        
    # Add travel mode
    params['travel_mode'] = travel_mode
    
    try:
        response = requests.get(
            f"{GEOCODING_SERVICE_URL}/api/calculate-distance",
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(
                f"Distance calculation failed with status {response.status_code}: "
                f"{response.text}"
            )
            # Return default values on failure
            return {
                "distance_km": float('inf'),
                "travel_time_minutes": float('inf'),
                "status": "error",
                "source": "fallback",
                "error": "Failed to calculate distance"
            }
    except Exception as e:
        logger.error(f"Error calculating distance: {str(e)}")
        # Return default values on exception
        return {
            "distance_km": float('inf'),
            "travel_time_minutes": float('inf'),
            "status": "error",
            "source": "fallback",
            "error": str(e)
        }


def find_nearby_therapists(
    patient_location: Dict[str, Any],
    therapists: List[Dict[str, Any]],
    max_distance_km: float,
    travel_mode: str = "car"
) -> List[Dict[str, Any]]:
    """Find therapists within a specific distance of a patient.
    
    Args:
        patient_location: Patient location data (address or coordinates)
        therapists: List of therapists to filter
        max_distance_km: Maximum distance in kilometers
        travel_mode: Mode of transport
        
    Returns:
        List of therapists with distance information
    """
    # Prepare request data
    patient_address = None
    patient_coords = None
    
    # Extract patient location
    if 'strasse' in patient_location and 'plz' in patient_location and 'ort' in patient_location:
        patient_address = (
            f"{patient_location['strasse']}, "
            f"{patient_location['plz']} {patient_location['ort']}"
        )
    
    # If we don't have a valid address, return empty list
    if not patient_address:
        logger.warning(f"Could not determine patient location")
        return []
    
    # Prepare therapist data for the request
    therapist_data = []
    for therapist in therapists:
        # Only include therapists with location data
        if 'strasse' in therapist and 'plz' in therapist and 'ort' in therapist:
            therapist_data.append({
                'id': therapist['id'],
                'strasse': therapist['strasse'],
                'plz': therapist['plz'],
                'ort': therapist['ort']
            })
    
    # If no therapists have location data, return empty list
    if not therapist_data:
        logger.warning("No therapists with valid location data")
        return []
        
    # Call the Geocoding Service to find nearby therapists
    try:
        data = {
            'patient_address': patient_address,
            'max_distance_km': max_distance_km,
            'travel_mode': travel_mode,
            'therapists': therapist_data
        }
        
        response = requests.post(
            f"{GEOCODING_SERVICE_URL}/api/find-therapists",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            # Return the therapists with distance information
            return result.get('therapists', [])
        else:
            logger.warning(
                f"Failed to find nearby therapists: {response.status_code} - {response.text}"
            )
            return []
    except Exception as e:
        logger.error(f"Error finding nearby therapists: {str(e)}")
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
    if max_distance is None:
        # Extract max distance from patient data
        patient_location_prefs = patient.get('raeumliche_verfuegbarkeit', {}) or {}
        max_distance = patient_location_prefs.get('max_km', 30.0)
    
    # Get list of excluded therapists
    excluded_ids = excluded_therapist_ids or []
    if patient.get('ausgeschlossene_therapeuten'):
        excluded_ids.extend(patient['ausgeschlossene_therapeuten'])
    
    # Get all active therapists
    therapists = get_all_therapists(status="ACTIVE")
    
    # Apply initial filters before distance calculation
    filtered_therapists = []
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
        
        # Add to filtered list
        filtered_therapists.append(therapist)
    
    # Get patient travel mode preference (default to car)
    travel_mode = "car"
    if patient.get('verkehrsmittel', '').lower() == 'öpnv':
        travel_mode = "transit"
    
    # Calculate distances and apply distance filter
    nearby_therapists = find_nearby_therapists(
        patient_location=patient,
        therapists=filtered_therapists,
        max_distance_km=max_distance,
        travel_mode=travel_mode
    )
    
    # Check for existing placement requests
    db = SessionLocal()
    try:
        final_matches = []
        
        for therapist in nearby_therapists:
            # Check if a placement request already exists
            existing_request = db.query(PlacementRequest).filter(
                PlacementRequest.patient_id == patient_id,
                PlacementRequest.therapist_id == therapist['id'],
                PlacementRequest.status != PlacementRequestStatus.REJECTED
            ).first()
            
            if existing_request:
                # Skip if already matched
                continue
                
            # Get full therapist data
            therapist_data = get_therapist_data(therapist['id'])
            
            # Create match result with distance info
            match = {
                'therapist_id': therapist['id'],
                'therapist_name': f"{therapist_data.get('vorname')} {therapist_data.get('nachname')}",
                'therapist_data': therapist_data,
                'distance_km': therapist['distance_km'],
                'travel_time_minutes': therapist['travel_time_minutes'],
                'travel_mode': therapist['travel_mode']
            }
            
            final_matches.append(match)
        
        return final_matches
    finally:
        db.close()


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