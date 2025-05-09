# Matching Service

## Summary
This document details the implementation of the Matching Service, the third microservice developed for the Psychotherapy Matching Platform. The service handles the matching algorithm between patients and therapists, including placement request management, matching criteria, and status tracking.

## Models Implementation

### Placement Request Model
The Placement Request model is implemented in `matching_service/models/placement_request.py` and serves as the core data structure representing a potential match between a patient and therapist. It includes:

- References to patient and therapist
- Status tracking for the request
- Contact history fields
- Response tracking
- Priority information
- Notes and additional metadata

### Status Enumeration
The `PlacementRequestStatus` enum defines the lifecycle of a placement request:
- OPEN: Initial state, match identified but not yet processed
- IN_PROGRESS: Being actively worked on (communication sent)
- REJECTED: Therapist has declined the placement
- ACCEPTED: Therapist has accepted the patient

## API Implementation

### Flask Application
The main Flask application is configured in `matching_service/app.py` with RESTful API endpoints and Kafka consumers.

### API Endpoints
Implemented in `matching_service/api/matching.py`:

#### PlacementRequestResource
Handles individual placement request operations:
- `GET /api/placement-requests/<id>`: Retrieve a specific placement request
- `PUT /api/placement-requests/<id>`: Update an existing placement request
- `DELETE /api/placement-requests/<id>`: Delete a placement request

#### PlacementRequestListResource
Handles collection operations:
- `GET /api/placement-requests`: Retrieve all placement requests with optional filtering
- `POST /api/placement-requests`: Create a new placement request

## Matching Algorithm

The service includes a matching algorithm implementation in the `matching_service/algorithms/matcher.py` file, which provides key functions:

### Finding Matching Therapists
The `find_matching_therapists()` function identifies suitable therapists for a patient based on multiple criteria:
- Patient location and therapist location (distance calculation)
- Patient gender preferences
- Excluded therapists list
- Therapist availability
- Previous placement requests (to avoid duplicates)

### Creating Placement Requests
The `create_placement_requests()` function handles creating multiple placement requests at once for efficient batch processing.

## Event Management

### Event Producers
The service implements Kafka producers for different matching events in `matching_service/events/producers.py`:
1. `match.created`: When a new placement request is created
2. `match.status_changed`: When a placement request's status changes

### Event Consumers
The service consumes events from both the Patient and Therapist services in `matching_service/events/consumers.py`:
- Reacting to patient deletion (canceling all their placement requests)
- Reacting to therapist blocking (suspending placement requests)
- Updating placement requests when patients or therapists change

## Service Integration

### Communication with Other Services
The matching service integrates with the Patient and Therapist services through:
1. REST API Calls: For direct data retrieval
2. Kafka Events: For asynchronous updates and notifications

## Docker Configuration
The Matching Service is containerized for consistent deployment. Configuration can be found in `matching_service/Dockerfile` and the service section in `docker-compose.yml`.

## Database Migration
A migration script creates the placement request table in the `matching_service` schema. This is managed through the project's Alembic configuration.

## Dependencies
All dependencies are listed in `matching_service/requirements.txt`.

## Testing

### Algorithm Testing
A test script is provided in `matching_service/tests/test_matching.py` for testing the matching algorithm with real data from the database.

## Future Enhancements

1. **Integration with Geocoding Service**: The current implementation includes placeholders for distance calculation that will be replaced with actual calculations once the Geocoding service is implemented.

2. **Advanced Matching Criteria**: The matching algorithm can be enhanced with additional criteria.

3. **Machine Learning Integration**: Future versions could incorporate machine learning for optimizing matching success rates based on historical data.