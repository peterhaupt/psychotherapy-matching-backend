# Kafka in Geocoding Service
## Event-Driven Architecture Documentation

---

## Overview
The Geocoding Service uses Apache Kafka for asynchronous, event-driven communication between microservices. It acts as both an event producer (publishing geocoding and distance calculation results) and an event consumer (processing geocoding and distance calculation requests from other services).

---

## Kafka as Event Producer

The geocoding service publishes events to the **`geocoding-events`** topic to notify other services about geocoding and distance calculation results.

### Published Events

#### 1. **`geocoding.distance_result`**
- **Trigger**: When a distance calculation is completed
- **Payload**:
  ```json
  {
    "request_id": string,
    "result": {
      "distance_km": float,
      "status": string,
      "source": string,
      "travel_mode": string,
      "route_available": boolean
    }
  }
  ```
- **Purpose**: Returns distance calculation results to requesting services
- **Source Types**: 
  - `"osrm"` - Route-based calculation via OpenStreetMap Routing Machine
  - `"haversine"` - Straight-line distance calculation
  - `"plz_centroids"` - Distance between postal code centroids
  - `"cache"` - Previously calculated and cached result

#### 2. **`geocoding.geocode_result`**
- **Trigger**: When an address is successfully geocoded to coordinates
- **Payload**:
  ```json
  {
    "request_id": string,
    "address": string,
    "coordinates": {
      "latitude": float,
      "longitude": float
    },
    "display_name": string (optional)
  }
  ```
- **Purpose**: Returns geocoded coordinates for addresses to requesting services

#### 3. **`geocoding.therapist_search_result`**
- **Trigger**: When a therapist proximity search is completed
- **Payload**:
  ```json
  {
    "request_id": string,
    "patient_location": {
      "latitude": float,
      "longitude": float,
      "address": string
    },
    "therapists": {
      "within_radius": [...],
      "total_found": int
    },
    "search_params": {
      "max_distance_km": float,
      "travel_mode": string
    }
  }
  ```
- **Purpose**: Returns therapists within specified distance from patient location

---

## Kafka as Event Consumer

The geocoding service consumes events from the **`geocoding-requests`** topic to handle geocoding and distance calculation requests from other services.

### Consumed Events

#### 1. **`geocoding.calculate_distance`**
- **Action**: Calculates distance between two points
- **Processing**:
  1. Extracts origin and destination from event payload
  2. Determines if inputs are addresses or coordinates
  3. Geocodes addresses if needed
  4. Checks cache for existing calculations
  5. Attempts route-based calculation via OSRM
  6. Falls back to haversine distance if routing fails
  7. Caches result for future use
  8. Publishes result via `geocoding.distance_result` event
- **Expected Payload**:
  ```json
  {
    "request_id": string,
    "origin": string or [latitude, longitude],
    "destination": string or [latitude, longitude],
    "travel_mode": string (optional, default: "car")
  }
  ```
- **Travel Modes**: `"car"`, `"transit"`

#### 2. **`geocoding.search_therapists`**
- **Action**: Finds therapists within specified distance from location
- **Processing**:
  1. Geocodes patient location if address provided
  2. Calculates distances to all therapists
  3. Filters therapists within maximum distance
  4. Returns sorted list by distance
- **Expected Payload**:
  ```json
  {
    "request_id": string,
    "patient_location": string or [latitude, longitude],
    "max_distance_km": float (optional),
    "travel_mode": string (optional)
  }
  ```
- **Note**: This event type is registered but implementation may be pending

---

## Caching Strategy

### Database Caching
The service maintains two cache tables to minimize external API calls:

#### 1. **GeoCache Table** (`geocoding_service.geocache`)
- **Purpose**: Stores geocoding results
- **Cached Data**:
  - Address to coordinate mappings
  - Reverse geocoding results
  - Full address components
- **Hit Tracking**: Increments counter on cache hits

#### 2. **DistanceCache Table** (`geocoding_service.distance_cache`)
- **Purpose**: Stores distance calculation results
- **Cached Data**:
  - Origin and destination coordinates
  - Calculated distance
  - Travel mode
  - Route data (if available)
- **Hit Tracking**: Increments counter on cache hits

### In-Memory Caching
- **Implementation**: TTLCache with configurable size and TTL
- **Default TTL**: Configured via `CACHE_TTL_SECONDS`
- **Max Size**: Configured via `CACHE_MAX_SIZE`
- **Purpose**: Reduces database queries for very frequent requests

---

## PLZ Centroid System

### Overview
The service maintains a database of German postal code (PLZ) centroids for fast approximate distance calculations.

### PLZ Centroids Table (`geocoding_service.plz_centroids`)
- **Data**: 5-digit German postal codes with centroid coordinates
- **Fields**:
  - `plz`: 5-digit postal code
  - `ort`: City/location name
  - `bundesland`: State name
  - `bundesland_code`: State code
  - `latitude`: Centroid latitude
  - `longitude`: Centroid longitude

### PLZ-Based Fallback
When precise geocoding fails, the service can:
1. Extract PLZ from address strings
2. Use PLZ centroids for approximate location
3. Calculate distance between PLZ centroids
4. Return result with `source: "plz_centroids"`

---

## External API Integration

### OpenStreetMap Nominatim
- **Purpose**: Address geocoding and reverse geocoding
- **Rate Limiting**: Configurable via `OSM_RATE_LIMIT`
- **Timeout**: Configurable via `OSM_TIMEOUT`
- **Retries**: Configurable via `OSM_MAX_RETRIES`
- **User Agent**: Configured via `OSM_USER_AGENT`

### OpenStreetMap Routing Machine (OSRM)
- **Purpose**: Route-based distance calculations
- **Profiles**: 
  - Car routing: `OSRM_PROFILE_CAR`
  - Transit routing: `OSRM_PROFILE_TRANSIT`
- **Fallback**: Haversine distance when routing fails

---

## Implementation Details

### Producer Implementation
```python
# Located in: geocoding_service/events/producers.py

from shared.kafka.robust_producer import RobustKafkaProducer

producer = RobustKafkaProducer(service_name="geocoding-service")
GEOCODING_TOPIC = "geocoding-events"

# Example: Publishing distance calculation result
def publish_distance_result(
    request_id: str,
    result: Dict[str, Any]
) -> bool:
    return producer.send_event(
        topic=GEOCODING_TOPIC,
        event_type="geocoding.distance_result",
        payload={
            "request_id": request_id,
            "result": result
        },
        key=str(request_id)
    )
```

### Consumer Implementation
```python
# Located in: geocoding_service/events/consumers.py

from shared.kafka import EventSchema, KafkaConsumer
from utils.distance import calculate_distance

def handle_geocoding_request(event: EventSchema) -> None:
    if event.event_type == "geocoding.calculate_distance":
        # Extract parameters
        payload = event.payload
        request_id = payload.get("request_id")
        origin = payload.get("origin")
        destination = payload.get("destination")
        travel_mode = payload.get("travel_mode", "car")
        
        # Calculate distance
        result = calculate_distance(
            origin, destination, travel_mode=travel_mode
        )
        
        # Publish result
        publish_distance_result(request_id, result)

# Start consumer
geocoding_consumer = KafkaConsumer(
    topics=["geocoding-requests"],
    group_id="geocoding-service",
)
```

---

## REST API Endpoints

The service also provides synchronous REST endpoints for direct access:

### Endpoints
- **`GET /api/geocode`** - Geocode address to coordinates
- **`GET /api/reverse-geocode`** - Convert coordinates to address
- **`GET /api/calculate-distance`** - Calculate distance between points
- **`GET /api/calculate-plz-distance`** - Calculate distance between PLZ codes
- **`GET /health`** - Service health check

### Example REST Request
```bash
GET /api/calculate-distance?origin=Berlin&destination=Munich&travel_mode=car
```

---

## Configuration

### Environment Variables
```bash
# OpenStreetMap Configuration
OSM_API_URL=https://nominatim.openstreetmap.org
OSM_USER_AGENT=curavani-geocoding-service
OSM_TIMEOUT=10
OSM_MAX_RETRIES=3
OSM_RATE_LIMIT=1.0

# OSRM Configuration
OSRM_API_URL=https://router.project-osrm.org
OSRM_PROFILE_CAR=driving
OSRM_PROFILE_TRANSIT=driving

# Cache Configuration
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
GEOCODING_REQUEST_TIMEOUT=30
GEOCODING_RETRY_DELAY_BASE=1.0
GEOCODING_RATE_LIMIT_SLEEP=1.0
GEOCODING_COORDINATE_PRECISION=6
```

---

## Error Handling

### Fallback Strategy
1. **Primary**: Try route-based distance (OSRM)
2. **Secondary**: Calculate haversine distance
3. **Tertiary**: Use PLZ centroid distance (if PLZ available)
4. **Final**: Return error status

### Status Codes
- `"success"` - Calculation completed successfully
- `"partial"` - Calculation completed with fallback method
- `"error"` - Calculation failed

---

## Performance Considerations

### Optimization Strategies
1. **Multi-layer caching**: In-memory → Database → External API
2. **Coordinate rounding**: 6 decimal places (~11cm precision) to improve cache hits
3. **Rate limiting**: Prevents API throttling
4. **Batch processing**: For multiple distance calculations
5. **PLZ fallback**: Fast approximate distances without external API calls

### Monitoring Metrics
- Cache hit rates (tracked via `hit_count` fields)
- External API call frequency
- Response times per calculation method
- Error rates by type

---

## Future Enhancements

### Planned Features
- Batch geocoding support
- Isochrone calculations (reachable areas within time/distance)
- Multi-modal routing (combining car, transit, walking)
- Traffic-aware distance calculations
- Historical distance data analysis

### Potential Improvements
- GraphQL API support
- WebSocket support for real-time updates
- Machine learning for address parsing
- Custom routing profiles
- Integration with additional geocoding providers