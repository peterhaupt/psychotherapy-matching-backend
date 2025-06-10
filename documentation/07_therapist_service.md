# Therapist Service

> **Note**: For API endpoint documentation, see `API_REFERENCE.md` which contains the complete API specification.

## Summary
This document details the implementation of the Therapist Service, the second microservice developed for the Psychotherapy Matching Platform. The service handles all therapist-related data and operations, including therapist profile management, availability tracking, and status management.

## Models Implementation

### Therapist Model
The Therapist model is implemented in `therapist_service/models/therapist.py` and includes:
- Personal and professional information fields
- Availability data in a structured JSON format
- Status tracking (active, blocked, inactive)
- Contact history tracking

The model also provides helper methods for availability management:
- `get_available_slots()` - Retrieves time slots for a specific date
- `is_available_at()` - Checks availability at a specific date and time
- `get_next_available_slot()` - Finds the next available appointment slot

### Status Enumeration
The `TherapistStatus` enum defines possible therapist states:
- ACTIVE: Therapist is available for matching
- BLOCKED: Therapist is temporarily blocked from receiving new matches
- INACTIVE: Therapist is no longer active in the system

## Event Management

### Event Producers
The service implements Kafka producers for different therapist events in `therapist_service/events/producers.py`:

1. `publish_therapist_created`: When a new therapist is created
2. `publish_therapist_updated`: When a therapist's data is updated
3. `publish_therapist_blocked`: When a therapist is blocked for new requests
4. `publish_therapist_unblocked`: When a previously blocked therapist is unblocked

### Event Consumers
A framework for consuming patient events is provided in `therapist_service/events/consumers.py`, allowing the therapist service to react to changes in patient data.

## Docker Configuration
The Therapist Service is containerized for consistent deployment. Configuration can be found in `therapist_service/Dockerfile` and the relevant service section in `docker-compose.yml`.

## Database Migration
A migration script creates the therapist table in the `therapist_service` schema. This is managed through the project's Alembic configuration.

## Dependencies
The therapist service has the following key dependencies:
- Flask and Flask-RESTful for API implementation
- SQLAlchemy for database operations
- Kafka-Python for event messaging
- PostgreSQL driver for database connectivity

All dependencies are listed in `therapist_service/requirements.txt`.

## Development Best Practices

The service follows these best practices:
1. **Error Handling**: Proper exception handling for database operations
2. **Code Structure**: Clear separation of models, API endpoints, and events
3. **Event Management**: Standardized event schema and comprehensive payload data