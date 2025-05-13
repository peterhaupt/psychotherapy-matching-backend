"""OpenStreetMap integration utilities."""
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union

import requests
from requests.exceptions import RequestException
from cachetools import TTLCache

from shared.utils.database import SessionLocal
from models.geocache import GeoCache
import config

# Initialize logging
logger = logging.getLogger(__name__)

# In-memory cache for very frequent requests
# This complements the database cache
in_memory_cache = TTLCache(
    maxsize=config.CACHE_MAX_SIZE,
    ttl=config.CACHE_TTL_SECONDS
)

# Track last request time for rate limiting
last_request_time = 0


def _rate_limit():
    """Implement rate limiting for API requests."""
    global last_request_time
    
    # Calculate time since last request
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    
    # Calculate required delay for rate limiting
    min_interval = 1.0 / config.OSM_RATE_LIMIT
    
    # Sleep if needed to respect rate limit
    if time_since_last_request < min_interval:
        sleep_time = min_interval - time_since_last_request
        time.sleep(sleep_time)
    
    # Update last request time
    last_request_time = time.time()


def _make_request(url: str, params: Dict[str, Any] = None) -> Optional[Dict]:
    """Make a request to the OpenStreetMap API with retries.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        
    Returns:
        Response JSON or None if failed
    """
    # Apply rate limiting
    _rate_limit()
    
    # Add common parameters
    headers = {"User-Agent": config.OSM_USER_AGENT}
    
    # Try with retries
    for attempt in range(config.OSM_MAX_RETRIES):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=config.OSM_TIMEOUT
            )
            
            # Log information about the request
            logger.debug(
                f"OSM API request: {url} with params {params}, "
                f"status: {response.status_code}"
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            
            # Handle error status
            if response.status_code == 429:  # Too Many Requests
                wait_time = min(2 ** attempt, 60)  # Exponential backoff
                logger.warning(
                    f"Rate limit exceeded, waiting for {wait_time} seconds"
                )
                time.sleep(wait_time)
            else:
                logger.warning(
                    f"Request failed with status {response.status_code}: "
                    f"{response.text}"
                )
        
        except RequestException as e:
            logger.error(f"Request error: {str(e)}")
            
        # Only sleep before retrying, not after the last attempt
        if attempt < config.OSM_MAX_RETRIES - 1:
            time.sleep(1)
    
    # If we get here, all attempts failed
    logger.error(
        f"All {config.OSM_MAX_RETRIES} attempts to request {url} failed"
    )
    return None


def geocode_address(address: str) -> Optional[Dict[str, Any]]:
    """Geocode an address to coordinates using Nominatim API with caching.
    
    Args:
        address: Address string to geocode
        
    Returns:
        Dict with lat, lon, and display_name, or None if geocoding failed
    """
    query_type = "address"
    
    # Normalize address for consistent caching
    normalized_address = address.strip().lower()
    
    # Check in-memory cache first
    cache_key = f"{query_type}:{normalized_address}"
    if cache_key in in_memory_cache:
        logger.debug(f"In-memory cache hit for '{normalized_address}'")
        return in_memory_cache[cache_key]
    
    # Check database cache
    db = SessionLocal()
    try:
        cache_entry = db.query(GeoCache).filter(
            GeoCache.query == normalized_address,
            GeoCache.query_type == query_type
        ).first()
        
        if cache_entry:
            # Update hit count
            cache_entry.hit_count += 1
            db.commit()
            
            # Parse the stored JSON
            result_data = json.loads(cache_entry.result_data)
            
            # Store in memory cache too
            in_memory_cache[cache_key] = result_data
            
            logger.debug(f"Database cache hit for '{normalized_address}'")
            return result_data
    
    except Exception as e:
        logger.error(f"Error accessing geocoding cache: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    # No cache hit, make the API request
    url = f"{config.OSM_API_URL}/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    
    # Make the request
    response_data = _make_request(url, params)
    if not response_data or len(response_data) == 0:
        logger.warning(f"Geocoding failed for address: '{address}'")
        return None
    
    # Extract the relevant data
    result = response_data[0]
    geocode_result = {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "display_name": result["display_name"],
        "address_components": result.get("address", {}),
        "source": "nominatim"
    }
    
    # Cache the result in database
    db = SessionLocal()
    try:
        cache_entry = GeoCache(
            query=normalized_address,
            query_type=query_type,
            latitude=geocode_result["latitude"],
            longitude=geocode_result["longitude"],
            display_name=geocode_result["display_name"],
            result_data=json.dumps(geocode_result)
        )
        db.add(cache_entry)
        db.commit()
        
        # Also cache in memory
        in_memory_cache[cache_key] = geocode_result
        
        logger.debug(f"Cached geocoding result for '{normalized_address}'")
    
    except Exception as e:
        logger.error(f"Error caching geocoding result: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    return geocode_result


def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """Convert coordinates to an address using Nominatim API with caching.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Dict with address information or None if geocoding failed
    """
    query_type = "coordinates"
    
    # Normalize coordinates (round to 6 decimal places - ~11cm precision)
    lat_rounded = round(latitude, 6)
    lon_rounded = round(longitude, 6)
    
    # Create a string representation for caching
    coord_str = f"{lat_rounded},{lon_rounded}"
    
    # Check in-memory cache first
    cache_key = f"{query_type}:{coord_str}"
    if cache_key in in_memory_cache:
        logger.debug(f"In-memory cache hit for coordinates '{coord_str}'")
        return in_memory_cache[cache_key]
    
    # Check database cache
    db = SessionLocal()
    try:
        cache_entry = db.query(GeoCache).filter(
            GeoCache.query == coord_str,
            GeoCache.query_type == query_type
        ).first()
        
        if cache_entry:
            # Update hit count
            cache_entry.hit_count += 1
            db.commit()
            
            # Parse the stored JSON
            result_data = json.loads(cache_entry.result_data)
            
            # Store in memory cache too
            in_memory_cache[cache_key] = result_data
            
            logger.debug(f"Database cache hit for coordinates '{coord_str}'")
            return result_data
    
    except Exception as e:
        logger.error(f"Error accessing coordinate geocoding cache: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    # No cache hit, make the API request
    url = f"{config.OSM_API_URL}/reverse"
    params = {
        "lat": lat_rounded,
        "lon": lon_rounded,
        "format": "json",
        "addressdetails": 1
    }
    
    # Make the request
    response_data = _make_request(url, params)
    if not response_data or "error" in response_data:
        logger.warning(
            f"Reverse geocoding failed for coordinates: {lat_rounded}, {lon_rounded}"
        )
        return None
    
    # Extract the relevant data
    geocode_result = {
        "display_name": response_data["display_name"],
        "address_components": response_data.get("address", {}),
        "latitude": lat_rounded,
        "longitude": lon_rounded,
        "source": "nominatim"
    }
    
    # Cache the result in database
    db = SessionLocal()
    try:
        cache_entry = GeoCache(
            query=coord_str,
            query_type=query_type,
            latitude=lat_rounded,
            longitude=lon_rounded,
            display_name=geocode_result["display_name"],
            result_data=json.dumps(geocode_result)
        )
        db.add(cache_entry)
        db.commit()
        
        # Also cache in memory
        in_memory_cache[cache_key] = geocode_result
        
        logger.debug(f"Cached reverse geocoding result for '{coord_str}'")
    
    except Exception as e:
        logger.error(f"Error caching reverse geocoding result: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    return geocode_result


def get_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    travel_mode: str = "car"
) -> Optional[Dict[str, Any]]:
    """Get a route between two points using OSRM API.
    
    Args:
        origin: Tuple of (latitude, longitude) for origin
        destination: Tuple of (latitude, longitude) for destination
        travel_mode: Mode of transport ('car' or 'transit')
        
    Returns:
        Dict with route information or None if routing failed
    """
    # Select the appropriate profile
    profile = (
        config.OSRM_PROFILE_CAR
        if travel_mode == "car"
        else config.OSRM_PROFILE_TRANSIT
    )
    
    # OSRM expects coordinates as longitude,latitude
    coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    
    # Build the request URL
    url = f"{config.OSRM_API_URL}/route/v1/{profile}/{coords}"
    params = {
        "overview": "simplified",
        "geometries": "geojson",
        "steps": "true",
        "annotations": "distance,duration"
    }
    
    # Make the request
    response_data = _make_request(url, params)
    if not response_data or response_data.get("code") != "Ok":
        logger.warning(
            f"Route calculation failed for {origin} to {destination} "
            f"with mode {travel_mode}"
        )
        return None
    
    # Extract the route information
    route = response_data["routes"][0]
    
    # Prepare result
    result = {
        "distance_meters": route["distance"],
        "distance_km": route["distance"] / 1000.0,
        "duration_seconds": route["duration"],
        "duration_minutes": route["duration"] / 60.0,
        "geometry": route.get("geometry"),
        "source": "osrm",
        "travel_mode": travel_mode
    }
    
    return result