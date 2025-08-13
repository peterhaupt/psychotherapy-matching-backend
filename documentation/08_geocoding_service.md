# Geocoding Service

## Overview
The Geocoding Service is responsible for all geocoding and distance calculation operations in the Therapy Matching Platform. It provides APIs for converting addresses to coordinates, calculating distances between locations, and finding therapists within a certain distance of a patient. The service uses centralized configuration for all external API settings and operational parameters.

## Features
- **Address Geocoding**: Convert addresses to geographic coordinates
- **Reverse Geocoding**: Convert coordinates to addresses
- **Distance Calculation**: Calculate distance and travel time between two points
- **Therapist Search**: Find therapists within a specified distance of a patient
- **Multi-level Caching**: Both in-memory and database caching to minimize API calls
- **Rate Limiting**: Automatic rate limiting for external API calls
- **Centralized Configuration**: All settings managed through shared configuration

## Centralized Configuration

All Geocoding Service settings are managed through `shared/config/settings.py`:

```python
from shared.config import get_config

config = get_config()

# OpenStreetMap settings
osm_api_url = config.OSM_API_URL  # Default: "https://nominatim.openstreetmap.org"
osm_user_agent = config.OSM_USER_AGENT  # Default: "TherapyPlatform/1.0"
osm_timeout = config.OSM_TIMEOUT  # Default: 10 seconds
osm_max_retries = config.OSM_MAX_RETRIES  # Default: 3
osm_rate_limit = config.OSM_RATE_LIMIT  # Default: 1.0 requests/second

# OSRM (routing) settings
osrm_api_url = config.OSRM_API_URL  # Default: "https://router.project-osrm.org"
osrm_profile_car = config.OSRM_PROFILE_CAR  # Default: "car"
osrm_profile_transit = config.OSRM_PROFILE_TRANSIT  # Default: "foot"

# Cache settings
cache_ttl = config.CACHE_TTL_SECONDS  # Default: 30 days
cache_max_size = config.CACHE_MAX_SIZE  # Default: 1000 entries
```

### Environment Variables
Geocoding settings in `.env`:
- `OSM_API_URL`: OpenStreetMap Nominatim API URL
- `OSM_USER_AGENT`: User agent string for OSM requests
- `OSM_TIMEOUT`: Request timeout in seconds
- `OSM_MAX_RETRIES`: Maximum retry attempts
- `OSM_RATE_LIMIT`: Requests per second limit
- `OSRM_API_URL`: OSRM routing API URL
- `OSRM_PROFILE_CAR`: OSRM profile for car routing
- `OSRM_PROFILE_TRANSIT`: OSRM profile for transit routing
- `CACHE_TTL_SECONDS`: Cache time-to-live in seconds
- `CACHE_MAX_SIZE`: Maximum in-memory cache size

## API Endpoints

### Geocoding
- **GET /api/geocode?address={address}**
  - Convert an address to coordinates
  - Returns latitude, longitude, and formatted address
  - Uses caching to minimize external API calls

### Reverse Geocoding
- **GET /api/reverse-geocode?lat={latitude}&lon={longitude}**
  - Convert coordinates to an address
  - Returns formatted address and address components
  - Implements coordinate rounding for cache efficiency

### Distance Calculation
- **GET /api/calculate-distance**
  - Calculate distance between two points
  - Parameters:
    - `origin`: Address or coordinates (origin_lat, origin_lon)
    - `destination`: Address or coordinates (destination_lat, destination_lon)
    - `travel_mode`: "car" or "transit" (default: "car")
    - `no_cache`: Bypass cache for fresh calculation (default: false)
  - Returns distance in kilometers and travel time in minutes
  - Falls back to Haversine formula if routing fails

### Therapist Search
- **POST /api/find-therapists**
  - Find therapists within a specified distance from a patient
  - Request body:
    - `patient_address` or `patient_lat`/`patient_lon`: Patient location
    - `max_distance_km`: Maximum distance in kilometers
    - `travel_mode`: "car" or "transit"
    - `therapists`: List of therapist data with addresses
  - Returns filtered list of therapists with distance information

## Technical Details

### OpenStreetMap Integration
The service integrates with OpenStreetMap APIs using centralized configuration:

```python
# In utils/osm.py
from shared.config import get_config

config = get_config()

# Rate limiting implementation
def _rate_limit():
    min_interval = 1.0 / config.OSM_RATE_LIMIT
    # ... rate limiting logic

# API request with configuration
def _make_request(url: str, params: Dict[str, Any] = None):
    headers = {"User-Agent": config.OSM_USER_AGENT}
    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=config.OSM_TIMEOUT
    )
    # ... retry logic using config.OSM_MAX_RETRIES
```

### Caching Mechanism
Two-level caching system with centralized configuration:

1. **In-memory TTL cache**:
   ```python
   from cachetools import TTLCache
   
   in_memory_cache = TTLCache(
       maxsize=config.CACHE_MAX_SIZE,
       ttl=config.CACHE_TTL_SECONDS
   )
   ```

2. **Database cache**:
   - Persistent storage for geocoding results
   - Hit counting for cache analytics
   - Configurable TTL for cache expiration

### Error Handling
- Graceful degradation to Haversine formula when routing fails
- Exponential backoff for API request retries (configured via `OSM_MAX_RETRIES`)
- Comprehensive logging of errors and warnings
- Rate limit compliance with configurable limits

## Usage Examples

### Geocoding an Address
```bash
curl "http://localhost:8005/api/geocode?address=Berlin,Germany"
```

### Calculating Distance
```bash
curl "http://localhost:8005/api/calculate-distance?origin=Berlin,Germany&destination=Munich,Germany&travel_mode=car"
```

### Finding Nearby Therapists
```bash
curl -X POST "http://localhost:8005/api/find-therapists" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_address": "Berlin, Germany",
    "max_distance_km": 30,
    "travel_mode": "car",
    "therapists": [
      {
        "id": 1,
        "strasse": "Example Street 1",
        "plz": "10115",
        "ort": "Berlin"
      }
    ]
  }'
```

## Integration with Matching Service
The Matching Service uses the Geocoding Service for distance-based matching:

```python
# In matching service
from shared.config import get_config

config = get_config()
geocoding_url = config.get_service_url("geocoding", internal=True)

# Calculate distance
response = requests.get(
    f"{geocoding_url}/api/calculate-distance",
    params={
        "origin": patient_address,
        "destination": therapist_address,
        "travel_mode": travel_mode
    }
)
```

## Configuration for Different Environments

### Development
Default configuration in `shared/config/settings.py`:
```python
OSM_API_URL = "https://nominatim.openstreetmap.org"
OSM_RATE_LIMIT = 1.0  # 1 request per second
CACHE_TTL_SECONDS = 2592000  # 30 days
```

### Production
Override via environment variables:
```bash
# Use a dedicated Nominatim instance
OSM_API_URL=https://nominatim.mycompany.com
OSM_RATE_LIMIT=10.0  # Higher rate limit
CACHE_TTL_SECONDS=604800  # 7 days for fresher data
```

### Testing
```bash
# Use mock endpoints
OSM_API_URL=http://mock-nominatim:8080
OSRM_API_URL=http://mock-osrm:8080
CACHE_TTL_SECONDS=60  # Short cache for testing
```

## Performance Considerations

1. **Rate Limiting**: Configurable rate limits prevent API abuse
2. **Caching Strategy**: Two-level caching reduces external API calls
3. **Coordinate Rounding**: 6 decimal places (~11cm precision) for cache efficiency
4. **Batch Processing**: Therapist search processes multiple locations efficiently
5. **Fallback Mechanisms**: Haversine formula when routing fails

## Best Practices

1. **Use Centralized Configuration**: Always use `shared.config` for settings
2. **Respect Rate Limits**: Configure appropriate rate limits for your usage
3. **Monitor Cache Hit Rates**: Adjust cache settings based on usage patterns
4. **Handle Errors Gracefully**: Always provide fallback options
5. **Log API Usage**: Monitor external API calls for cost management
6. **Test with Different Modes**: Verify both car and transit routing work

## Troubleshooting

### Common Issues

1. **Rate Limit Errors**:
   - Check `OSM_RATE_LIMIT` setting
   - Monitor logs for 429 errors
   - Consider using a dedicated Nominatim instance

2. **Cache Misses**:
   - Verify `CACHE_TTL_SECONDS` is appropriate
   - Check database cache table for data
   - Monitor in-memory cache size

3. **Routing Failures**:
   - Verify OSRM API is accessible
   - Check if coordinates are routable
   - Fallback to Haversine works correctly

4. **Configuration Issues**:
   - Verify `.env` file has correct values
   - Check if configuration is loaded: `print(config.OSM_API_URL)`
   - Ensure shared package is in Python path

## Future Enhancements

1. **Additional Geocoding Providers**: Support for Google Maps, Mapbox
2. **Advanced Routing**: Multi-modal transportation, traffic consideration
3. **Batch Geocoding**: Process multiple addresses in single request
4. **Geographic Clustering**: Group therapists by geographic regions
5. **Real-time Traffic**: Integration with traffic data providers
6. **Accessibility Routing**: Routes considering accessibility needs