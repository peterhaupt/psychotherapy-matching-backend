# Patient Service

> **Note**: For complete API documentation, see `API_REFERENCE.md`

## Summary
First microservice developed, handles all patient-related operations including profile management, medical information, preferences, and communication tracking.

## Key Components

### Models (`patient_service/models/patient.py`)
- **Patient**: Core model with German field names
- **PatientStatus**: German enum values (offen, auf_der_Suche, etc.)
- **TherapistGenderPreference**: German enum values (Männlich, Weiblich, Egal)

### API Endpoints
1. **CRUD Operations**: Standard REST endpoints (see API_REFERENCE.md)
2. **Communication History** (NEW): `GET /api/patients/{id}/communication`
   - Fetches all emails and phone calls for a patient
   - Combines data from Communication Service
   - Returns sorted communication timeline

### Communication Utilities (`patient_service/utils/communication.py`)
Helper functions for patient communication:
- `send_patient_email()`: Send emails via Communication Service
- `schedule_patient_call()`: Schedule phone calls
- `send_welcome_email()`: Automated welcome message
- `send_status_update_email()`: Progress updates
- `send_match_found_email()`: Therapy match notifications

### Event Management
**Publishers** (`events/producers.py`):
- `patient.created`
- `patient.updated` 
- `patient.deleted`

Uses `RobustKafkaProducer` for resilient messaging.

## Integration Points
- **Communication Service**: For sending emails/scheduling calls
- **Matching Service**: Patient data consumed for bundle creation
- **Database**: Schema `patient_service` with `patienten` table

## Configuration
All settings managed through `shared.config`:
- Database connection via PgBouncer
- Service ports and URLs
- Kafka configuration

## Best Practices
1. **Error Handling**: All operations wrapped in try-except
2. **German Consistency**: Field names and enum values in German
3. **Date Handling**: ISO format (YYYY-MM-DD) for all dates
4. **Last Contact Tracking**: Auto-updated when communication sent