"""Documentation for the Geocoding Service."""

# Geocoding Service

## Overview
The Geocoding Service is responsible for all geocoding and distance calculation operations in the Therapy Matching Platform. It provides APIs for converting addresses to coordinates, calculating distances between locations, and finding therapists within a certain distance of a patient.

## Features
- **Address Geocoding**: Convert addresses to geographic coordinates
- **Reverse Geocoding**: Convert coordinates to addresses
- **Distance Calculation**: Calculate distance and travel time between two points
- **Therapist Search**: Find therapists within a specified distance of a patient
- **Multi-level Caching**: Both in-memory and database caching to minimize API calls
- **Rate Limiting**: Automatic rate limiting for external API calls

## API Endpoints

### Geocoding
- **GET /api/geocode?address={address}**
  - Convert an address to coordinates
  - Returns latitude, longitude, and formatted address

### Reverse Geocoding
- **GET /api/reverse-geocode?lat={latitude}&lon={longitude}**
  - Convert coordinates to an address
  - Returns formatted address and address components

### Distance Calculation
- **GET /api/calculate-distance**
  - Calculate distance between two points
  - Parameters:
    - `origin`: Address or coordinates (origin_lat, origin_lon)
    - `destination`: Address or coordinates (destination_lat, destination_lon)
    - `travel_mode`: "car" or "transit" (default: "car")
    - `no_cache`: Bypass cache for fresh calculation (default: false)
  - Returns distance in kilometers and travel time in minutes

### Therapist Search
- **POST /api/find-therapists**
  - Find therapists within a specified distance from a patient
  - Request body:
    - `patient_address` or `patient_lat`/`patient_lon`: Patient location
    - `max_distance_km`: Maximum distance in kilometers
    - `travel_mode`: "car" or "transit"
    - `therapists`: List of therapist data with addresses
  - Returns filtered list of therapists with distance information

## Kafka Events

### Consumed Events
- **geocoding.calculate_distance**
  - Process a distance calculation request asynchronously
  - Parameters:
    - `request_id`: Unique identifier for the request
    - `origin`: Origin address or coordinates
    - `destination`: Destination address or coordinates
    - `travel_mode`: "car" or "transit"

### Published Events
- **geocoding.distance_result**
  - Contains result of a distance calculation
  - Payload includes distance in kilometers and travel time in minutes

## Technical Details

### OpenStreetMap Integration
- Uses Nominatim API for geocoding operations
- Uses OSRM API for routing and distance calculations
- Respects OSM usage policy with rate limiting

### Caching Mechanism
- In-memory TTL cache for frequently accessed geocoding results
- Database cache with hit counting for long-term storage
- Configurable cache TTL and size

### Error Handling
- Graceful degradation to Haversine formula when routing fails
- Exponential backoff for API request retries
- Comprehensive logging of errors and warnings

## Usage Examples

### Geocoding an Address
```bash
curl "http://localhost:8005/api/geocode?address=Berlin,Germany"
```

### Calculating Distance
```bash
curl "http://localhost:8005/api/calculate-distance?origin=Berlin,Germany&destination=Munich,Germany&travel_mode=car"
```

## Integration with Matching Service
The Matching Service now uses the Geocoding Service to calculate distances between patients and therapists, allowing for more accurate matching based on location preferences.