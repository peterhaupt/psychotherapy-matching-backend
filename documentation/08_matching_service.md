# Matching Service

## Overview
The Matching Service handles the matching algorithm between patients and therapists, including placement request management and status tracking. The service is fully implemented with all business requirements.

## Implementation

### Models
- **PlacementRequest** (`models/placement_request.py`): Core data structure for patient-therapist matches
- **PlacementRequestStatus**: Enum tracking request lifecycle (open → in_progress → rejected/accepted)

### API Endpoints
See `api/matching.py` for implementation:

#### Placement Requests
- `GET /api/placement-requests` - List with filtering by patient/therapist/status
- `POST /api/placement-requests` - Create new placement request
- `GET /api/placement-requests/{id}` - Get specific request
- `PUT /api/placement-requests/{id}` - Update request status
- `DELETE /api/placement-requests/{id}` - Delete request

### Matching Algorithm
Implementation in `algorithms/matcher.py`:

1. **find_matching_therapists(patient_id)**
   - Retrieves patient data and preferences
   - Filters therapists by: status (active only), gender preference, exclusion list
   - Calculates distances using Geocoding Service
   - Filters by patient's maximum distance preference
   - Excludes therapists with existing placement requests
   - Returns sorted list by distance

2. **create_placement_requests(patient_id, therapist_ids, notes)**
   - Creates placement requests in bulk
   - Publishes creation events
   - Returns list of created request IDs

### Service Integration
- **Patient Service**: Retrieves patient data and preferences
- **Therapist Service**: Fetches active therapists
- **Geocoding Service**: Calculates distances based on patient's travel mode (car/transit)

### Event Management

#### Published Events
- `match.created`: New placement request created
- `match.status_changed`: Request status updated

#### Consumed Events  
- `patient.deleted`: Cancels all open requests for deleted patient
- `therapist.blocked`: Rejects all open requests for blocked therapist

## Configuration
All service URLs configured via `shared/config/settings.py`. No hardcoded endpoints.

## Key Business Rules
- Distance calculated using patient's specified travel mode (`verkehrsmittel`)
- Gender preferences respected (including "Egal" = any)
- Excluded therapists filtered out
- No duplicate placement requests created
- Only active therapists considered

## Error Handling
- Graceful degradation when external services unavailable
- Proper HTTP status codes returned
- Database transactions with rollback on errors