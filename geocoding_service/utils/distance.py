"""Distance calculation utilities."""
import json
import logging
from typing import Dict, Optional, Tuple, Any, List, Union

import haversine
from haversine import Unit

from shared.utils.database import SessionLocal
from models.geocache import DistanceCache
from utils.osm import get_route, geocode_address
from shared.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


def calculate_haversine_distance(
    origin: Tuple[float, float],
    destination: Tuple[float, float]
) -> float:
    """Calculate the distance between two points using the haversine formula.
    
    Args:
        origin: Tuple of (latitude, longitude) for origin
        destination: Tuple of (latitude, longitude) for destination
        
    Returns:
        Distance in kilometers
    """
    try:
        # The haversine library expects (lat, lon) tuples
        distance = haversine.haversine(origin, destination, unit=Unit.KILOMETERS)
        return round(distance, 2)
    except Exception as e:
        logger.error(f"Error calculating haversine distance: {str(e)}")
        return 0.0


def calculate_distance(
    origin: Union[str, Tuple[float, float]],
    destination: Union[str, Tuple[float, float]],
    travel_mode: str = "car",
    use_cache: bool = True
) -> Dict[str, Any]:
    """Calculate distance and travel time between two points.
    
    Args:
        origin: Origin address or coordinates (latitude, longitude)
        destination: Destination address or coordinates
        travel_mode: Mode of transport ("car" or "transit")
        use_cache: Whether to use cached results
        
    Returns:
        Dict with distance and travel time information
    """
    # Step 1: Convert addresses to coordinates if needed
    origin_coords = _ensure_coordinates(origin)
    destination_coords = _ensure_coordinates(destination)
    
    if origin_coords is None or destination_coords is None:
        logger.warning("Could not resolve coordinates for distance calculation")
        return {
            "distance_km": 0,
            "travel_time_minutes": 0,
            "status": "error",
            "error": "Could not resolve coordinates"
        }
    
    # Step 2: Check cache if requested
    if use_cache:
        cached_result = _get_cached_distance(
            origin_coords, destination_coords, travel_mode
        )
        if cached_result:
            return cached_result
    
    # Step 3: Try to get route information
    route_result = get_route(origin_coords, destination_coords, travel_mode)
    
    if route_result:
        # Cache the result
        _cache_distance_result(
            origin_coords,
            destination_coords,
            travel_mode,
            route_result
        )
        
        return {
            "distance_km": route_result["distance_km"],
            "travel_time_minutes": route_result["duration_minutes"],
            "status": "success",
            "source": "osrm",
            "travel_mode": travel_mode,
            "route_available": True
        }
    
    # Step 4: Fallback to haversine distance if route calculation fails
    haversine_distance = calculate_haversine_distance(
        origin_coords, destination_coords
    )
    
    # Estimate travel time based on average speeds
    # Car: 60 km/h, Transit: 15 km/h (very rough estimate)
    avg_speed = 60 if travel_mode == "car" else 15
    estimated_time = (haversine_distance / avg_speed) * 60  # minutes
    
    result = {
        "distance_km": haversine_distance,
        "travel_time_minutes": round(estimated_time, 1),
        "status": "partial",
        "source": "haversine",
        "travel_mode": travel_mode,
        "route_available": False
    }
    
    # Cache this result too
    _cache_distance_result(
        origin_coords,
        destination_coords,
        travel_mode,
        result
    )
    
    return result


def _ensure_coordinates(
    location: Union[str, Tuple[float, float]]
) -> Optional[Tuple[float, float]]:
    """Ensure location is in coordinate form.
    
    Args:
        location: Address string or coordinates tuple
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    # If already coordinates, just return them
    if isinstance(location, tuple) and len(location) == 2:
        return location
    
    # If string, geocode the address
    if isinstance(location, str):
        geocode_result = geocode_address(location)
        if geocode_result:
            return (geocode_result["latitude"], geocode_result["longitude"])
    
    # If we get here, we couldn't resolve coordinates
    return None


def _get_cached_distance(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    travel_mode: str
) -> Optional[Dict[str, Any]]:
    """Get cached distance calculation if available.
    
    Args:
        origin: Origin coordinates (latitude, longitude)
        destination: Destination coordinates
        travel_mode: Mode of transport
        
    Returns:
        Dict with distance information or None if not cached
    """
    # Round coordinates to reduce cache fragmentation
    origin_lat = round(origin[0], 6)
    origin_lon = round(origin[1], 6)
    dest_lat = round(destination[0], 6)
    dest_lon = round(destination[1], 6)
    
    db = SessionLocal()
    try:
        cache_entry = db.query(DistanceCache).filter(
            DistanceCache.origin_latitude == origin_lat,
            DistanceCache.origin_longitude == origin_lon,
            DistanceCache.destination_latitude == dest_lat,
            DistanceCache.destination_longitude == dest_lon,
            DistanceCache.travel_mode == travel_mode
        ).first()
        
        if cache_entry:
            # Update hit count
            cache_entry.hit_count += 1
            db.commit()
            
            # Parse route data if available
            route_data = None
            if cache_entry.route_data:
                try:
                    route_data = json.loads(cache_entry.route_data)
                except:
                    pass
            
            # Return the cached result
            return {
                "distance_km": cache_entry.distance_km,
                "travel_time_minutes": cache_entry.travel_time_minutes,
                "status": "success",
                "source": "cache",
                "travel_mode": travel_mode,
                "route_available": route_data is not None,
                "route": route_data
            }
        
        return None
    
    except Exception as e:
        logger.error(f"Error accessing distance cache: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()


def _cache_distance_result(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    travel_mode: str,
    result: Dict[str, Any]
) -> bool:
    """Cache a distance calculation result.
    
    Args:
        origin: Origin coordinates (latitude, longitude)
        destination: Destination coordinates
        travel_mode: Mode of transport
        result: The result to cache
        
    Returns:
        True if caching was successful, False otherwise
    """
    # Round coordinates to reduce cache fragmentation
    origin_lat = round(origin[0], 6)
    origin_lon = round(origin[1], 6)
    dest_lat = round(destination[0], 6)
    dest_lon = round(destination[1], 6)
    
    db = SessionLocal()
    try:
        # Check if entry already exists
        existing = db.query(DistanceCache).filter(
            DistanceCache.origin_latitude == origin_lat,
            DistanceCache.origin_longitude == origin_lon,
            DistanceCache.destination_latitude == dest_lat,
            DistanceCache.destination_longitude == dest_lon,
            DistanceCache.travel_mode == travel_mode
        ).first()
        
        if existing:
            # Update existing entry
            existing.distance_km = result["distance_km"]
            existing.travel_time_minutes = result["travel_time_minutes"]
            existing.route_data = json.dumps(result) if result else None
            existing.hit_count += 1
        else:
            # Create new entry
            cache_entry = DistanceCache(
                origin_latitude=origin_lat,
                origin_longitude=origin_lon,
                destination_latitude=dest_lat,
                destination_longitude=dest_lon,
                travel_mode=travel_mode,
                distance_km=result["distance_km"],
                travel_time_minutes=result["travel_time_minutes"],
                route_data=json.dumps(result) if result else None
            )
            db.add(cache_entry)
        
        db.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error caching distance result: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def find_nearby_therapists(
    patient_location: Union[str, Tuple[float, float]],
    therapists: List[Dict[str, Any]],
    max_distance_km: float = 30.0,
    travel_mode: str = "car"
) -> List[Dict[str, Any]]:
    """Find therapists within a specified distance from a patient.
    
    Args:
        patient_location: Patient address or coordinates
        therapists: List of therapist data with address or coordinates
        max_distance_km: Maximum distance in kilometers
        travel_mode: Mode of transport
        
    Returns:
        Filtered list of therapists with distance information added
    """
    # Ensure patient coordinates
    patient_coords = _ensure_coordinates(patient_location)
    if not patient_coords:
        logger.warning(f"Could not geocode patient location: {patient_location}")
        return []
    
    results = []
    
    for therapist in therapists:
        # Extract therapist location
        therapist_location = None
        
        # Check for coordinates
        if 'latitude' in therapist and 'longitude' in therapist:
            therapist_location = (therapist['latitude'], therapist['longitude'])
        # Otherwise try to build address from components
        elif all(key in therapist for key in ['strasse', 'plz', 'ort']):
            therapist_address = f"{therapist['strasse']}, {therapist['plz']} {therapist['ort']}"
            therapist_location = therapist_address
        # No location available
        else:
            logger.warning(f"No location data for therapist {therapist.get('id')}")
            continue
        
        # Calculate distance
        distance_result = calculate_distance(
            patient_coords, therapist_location, travel_mode
        )
        
        # Skip if exceeds maximum distance
        if distance_result["distance_km"] > max_distance_km:
            continue
        
        # Add distance info to therapist data
        therapist_with_distance = therapist.copy()
        therapist_with_distance.update({
            'distance_km': distance_result["distance_km"],
            'travel_time_minutes': distance_result["travel_time_minutes"],
            'travel_mode': travel_mode
        })
        
        results.append(therapist_with_distance)
    
    # Sort by distance
    results.sort(key=lambda x: x['distance_km'])
    
    return results