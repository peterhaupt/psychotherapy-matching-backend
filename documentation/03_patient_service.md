# Patient Service

## Summary
This document details the implementation of the Patient Service, the first microservice developed for the Psychotherapy Matching Platform. The service handles all patient-related data and operations, including patient profile management, medical information handling, preference tracking, and patient state management.

## Design Approach
The Patient Service was implemented first to establish core patterns that would be used across the platform:
- Domain-driven design principles
- RESTful API patterns
- Event-based communication
- Shared database access utilities

## Models Implementation

### Patient Model
The Patient model is implemented in `patient_service/models/patient.py` and includes:
- Personal information fields (name, contact details)
- Medical information (diagnosis, treatment history)
- Process status tracking fields
- Availability and preferences
- Therapist exclusions and gender preferences

For specific fields and implementation details, refer to the model file directly.

### Status Enumerations
Two key enum types define patient states:
- `PatientStatus`: Tracks the current phase of the patient in the process (open, searching, in therapy, etc.)
- `TherapistGenderPreference`: Captures patient preference for therapist gender

## API Implementation

### Flask Application
The main Flask application is configured in `patient_service/app.py`, establishing REST endpoints and database connectivity.

### API Endpoints
Implemented in `patient_service/api/patients.py`:

#### PatientResource
Handles individual patient operations:
- `GET /api/patients/<id>`: Retrieve a specific patient
- `PUT /api/patients/<id>`: Update an existing patient
- `DELETE /api/patients/<id>`: Delete a patient

#### PatientListResource
Handles collection operations:
- `GET /api/patients`: Retrieve all patients with optional filtering
- `POST /api/patients`: Create a new patient

## Event Management
The Patient Service publishes events when patient data changes, allowing other services to react to these changes without tight coupling.

### Event Types
- `patient.created`: When a new patient is registered
- `patient.updated`: When patient information changes
- `patient.deleted`: When a patient is removed

Event producers are defined in `patient_service/events/producers.py`.

## Docker Configuration
The Patient Service is containerized for consistent deployment using Docker. Configuration can be found in `patient_service/Dockerfile` and the service section in `docker-compose.yml`.

## Dependencies
The patient service has the following key dependencies:
- Flask and Flask-RESTful for API implementation
- SQLAlchemy for database operations
- Kafka-Python for event messaging
- PostgreSQL driver for database connectivity

## Development Best Practices

1. **Error Handling**:
   - All database operations are wrapped in try-except blocks
   - SQLAlchemy errors are properly handled and meaningful error messages returned
   - Consistent HTTP status codes (404 for not found, 500 for database errors)

2. **Code Structure**:
   - Separation of concerns: models, API endpoints
   - Consistent naming conventions
   - Proper docstrings and type hints
   - Flake8 compliance

3. **Database Operations**:
   - Proper session management (open, commit, close)
   - Rollbacks in case of errors
   - Transaction consistency