"""Distance calculation utilities."""
import json
import logging
from typing import Dict, Optional, Tuple, Any, List, Union

import haversine
from haversine import Unit
from sqlalchemy import text

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


def get_plz_centroid(plz: str) -> Optional[Tuple[float, float]]:
    """Get centroid coordinates for a PLZ code.
    
    Args:
        plz: German postal code
        
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT latitude, longitude 
            FROM geocoding_service.plz_centroids 
            WHERE plz = :plz
        """), {'plz': plz}).fetchone()
        
        if result:
            return (result.latitude, result.longitude)
        return None
        
    finally:
        db.close()


def calculate_plz_distance(
    origin_plz: str,
    destination_plz: str
) -> Optional[Dict[str, Any]]:
    """Calculate distance between two PLZ centroids.
    
    Args:
        origin_plz: Origin postal code
        destination_plz: Destination postal code
        
    Returns:
        Dict with distance information or None if PLZ not found
    """
    # Get centroids
    origin_coords = get_plz_centroid(origin_plz)
    destination_coords = get_plz_centroid(destination_plz)
    
    if not origin_coords or not destination_coords:
        logger.warning(f"PLZ centroid not found for {origin_plz if not origin_coords else destination_plz}")
        return None
    
    # Calculate Haversine distance
    distance_km = calculate_haversine_distance(origin_coords, destination_coords)
    
    return {
        "distance_km": distance_km,
        "status": "success",
        "source": "plz_centroids",
        "origin_centroid": {
            "latitude": origin_coords[0],
            "longitude": origin_coords[1]
        },
        "destination_centroid": {
            "latitude": destination_coords[0],
            "longitude": destination_coords[1]
        }
    }


def extract_plz_from_address(address: str) -> Optional[str]:
    """Extract PLZ (postal code) from an address string.
    
    Args:
        address: Address string that may contain a PLZ
        
    Returns:
        5-digit PLZ string or None if not found
    """
    import re
    
    # Look for 5-digit number that could be a German PLZ
    plz_pattern = r'\b(\d{5})\b'
    matches = re.findall(plz_pattern, address)
    
    for match in matches:
        # German PLZ range is 01001-99998
        if 1001 <= int(match) <= 99998:
            return match
    
    return None


def calculate_distance(
    origin: Union[str, Tuple[float, float]],
    destination: Union[str, Tuple[float, float]],
    travel_mode: str = "car",
    use_cache: bool = True,
    use_plz_fallback: bool = True
) -> Dict[str, Any]:
    """Calculate distance between two points.
    
    Args:
        origin: Origin address or coordinates (latitude, longitude)
        destination: Destination address or coordinates
        travel_mode: Mode of transport ("car" or "transit")
        use_cache: Whether to use cached results
        use_plz_fallback: Whether to use PLZ-based fallback for addresses
        
    Returns:
        Dict with distance information
    """
    # Step 1: Convert addresses to coordinates if needed
    origin_coords = _ensure_coordinates(origin)
    destination_coords = _ensure_coordinates(destination)
    
    if origin_coords is None or destination_coords is None:
        # Try PLZ fallback if enabled and inputs are addresses
        if use_plz_fallback and isinstance(origin, str) and isinstance(destination, str):
            origin_plz = extract_plz_from_address(origin)
            destination_plz = extract_plz_from_address(destination)
            
            if origin_plz and destination_plz:
                plz_result = calculate_plz_distance(origin_plz, destination_plz)
                if plz_result:
                    plz_result["travel_mode"] = travel_mode
                    plz_result["route_available"] = False
                    plz_result["note"] = "Approximate distance based on postal code areas"
                    return plz_result
        
        logger.warning("Could not resolve coordinates for distance calculation")
        return {
            "distance_km": 0,
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
        # Cache the result with original source
        cache_data = {
            "distance_km": route_result["distance_km"],
            "status": "success",
            "source": "osrm",
            "travel_mode": travel_mode,
            "route_available": True,
            "original_source": "osrm"  # Store original source
        }
        _cache_distance_result(
            origin_coords,
            destination_coords,
            travel_mode,
            cache_data
        )
        
        # Return without original_source field
        return {
            "distance_km": route_result["distance_km"],
            "status": "success",
            "source": "osrm",
            "travel_mode": travel_mode,
            "route_available": True
        }
    
    # Step 4: Fallback to haversine distance if route calculation fails
    haversine_distance = calculate_haversine_distance(
        origin_coords, destination_coords
    )
    
    result = {
        "distance_km": haversine_distance,
        "status": "partial",
        "source": "haversine",
        "travel_mode": travel_mode,
        "route_available": False,
        "original_source": "haversine"  # Store original source
    }
    
    # Cache this result too
    _cache_distance_result(
        origin_coords,
        destination_coords,
        travel_mode,
        result
    )
    
    # Return without original_source field
    return {
        "distance_km": haversine_distance,
        "status": "partial",
        "source": "haversine",
        "travel_mode": travel_mode,
        "route_available": False
    }


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
    
    # If string, try PLZ lookup first, then geocode the address
    if isinstance(location, str):
        # Try to extract PLZ for fast lookup
        plz = extract_plz_from_address(location)
        if plz:
            coords = get_plz_centroid(plz)
            if coords:
                logger.debug(f"Using PLZ centroid for {plz}")
                return coords
        
        # Fall back to geocoding
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
            original_source = "osrm"  # Default
            if cache_entry.route_data:
                try:
                    route_data = json.loads(cache_entry.route_data)
                    # Get original source if stored
                    original_source = route_data.get("original_source", route_data.get("source", "osrm"))
                except:
                    pass
            
            # Return the cached result with 'cache' as the source
            # Note: This indicates the data came from cache, which is useful information
            return {
                "distance_km": cache_entry.distance_km,
                "status": "success",
                "source": "cache",  # Indicates this came from cache
                "travel_mode": travel_mode,
                "route_available": route_data is not None
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