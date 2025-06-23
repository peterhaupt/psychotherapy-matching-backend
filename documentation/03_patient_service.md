# Patient Service

> **Note**: For complete API documentation, see `API_REFERENCE.md`

## Summary
First microservice developed for the Psychotherapy Matching Platform. Handles all patient-related operations including profile management, medical information, therapy preferences, and communication tracking with full German field naming consistency.

## Key Components

### Models (`patient_service/models/patient.py`)
- **Patient**: Core model with comprehensive German field names
- **PatientStatus**: German enum values (`offen`, `auf_der_Suche`, `in_Therapie`, etc.)
- **TherapistGenderPreference**: German enum values (`Männlich`, `Weiblich`, `Egal`)
- **Therapieverfahren**: German therapy procedure enums

### Database Schema Features
- **German field names**: `vorname`, `nachname`, `strasse`, `plz`, `ort`
- **Medical information**: `diagnose`, `symptome`, `erfahrung_mit_psychotherapie`
- **Preferences**: `bevorzugtes_therapieverfahren`, `bevorzugtes_therapeutengeschlecht`
- **Availability**: `zeitliche_verfuegbarkeit`, `raeumliche_verfuegbarkeit` (JSONB)
- **Process tracking**: `status`, `letzter_kontakt`, therapy placement dates

### API Endpoints
Standard REST operations with German field support:
- **CRUD Operations**: Create, read, update, delete patients
- **Status Management**: Patient status transitions through therapy journey
- **Communication History**: Integrated endpoint fetching emails and calls from Communication Service
- **Filtering**: Search by status and other criteria
- **Pagination**: All list endpoints support pagination

### Communication Integration (`patient_service/utils/communication.py`)
Helper functions for patient communication:
- `send_patient_email()`: Send emails via Communication Service with markdown support
- `schedule_patient_call()`: Schedule phone calls with patients
- **Automatic tracking**: Updates `letzter_kontakt` field when communication is sent

Pre-built communication functions:
- Welcome emails for new patients
- Status update notifications
- Therapy match found notifications
- Progress tracking communications

### Event Management
**Publishers** (`events/producers.py`):
- `patient.created` - New patient registration
- `patient.updated` - Patient information changes
- `patient.deleted` - Patient removal from system

Uses `RobustKafkaProducer` for resilient event messaging across services.

## Integration Points

### With Communication Service
- **Email creation**: Markdown-based emails with legal footer support
- **Phone scheduling**: Automatic and manual call scheduling
- **History tracking**: Combined view of all patient communications
- **Response tracking**: Monitors email responses and call outcomes

### With Matching Service
- **Search creation**: Patient data consumed for anfrage composition
- **Preference matching**: Therapy preferences used in therapist selection
- **Status updates**: Search success triggers patient status changes
- **Exclusion management**: Tracks excluded therapists per patient

### With Geocoding Service
- **Distance calculation**: Patient addresses used for travel distance constraints
- **Location validation**: Address verification and geocoding

## Configuration
All settings managed through `shared.config`:
- Database connection via PgBouncer
- Service ports and URLs
- Kafka configuration
- CORS settings for frontend integration

## Data Consistency Features

### German Naming Convention
- **Database fields**: All use German names (`geburtsdatum`, `krankenkasse`)
- **Enum values**: German status values (`auf_der_Suche`, `in_Therapie`)
- **API consistency**: Input and output maintain German field names
- **Validation**: Proper enum validation with German values

### Field Validation
- **Required fields**: `vorname`, `nachname` for patient creation
- **Date formats**: ISO format (YYYY-MM-DD) for all date fields
- **Status transitions**: Validates allowed status changes
- **Preference validation**: Ensures valid therapy procedure selections

### Backward Compatibility
- **Flexible updates**: Partial updates supported for all fields
- **Null handling**: Graceful handling of optional fields
- **Default values**: Sensible defaults for new patient creation

## Business Logic

### Patient Journey Tracking
- **Status progression**: From `offen` through `auf_der_Suche` to therapy completion
- **Timeline tracking**: Key dates for therapy search and placement
- **Communication history**: Complete audit trail of all interactions

### Preference Management
- **Therapy methods**: Support for multiple preferred therapy approaches
- **Therapist preferences**: Gender, age, and other therapist characteristics
- **Availability**: Complex time and location preference handling
- **Exclusions**: Maintains list of excluded therapists with reasons

### Medical Information Handling
- **Diagnosis codes**: ICD-10 diagnosis support
- **Symptoms tracking**: Free-text symptom descriptions
- **Therapy experience**: Previous therapy experience documentation
- **Medical history**: Comprehensive medical background information

## Best Practices Implementation
- **Error Handling**: All database operations wrapped in try-except blocks
- **Event Publishing**: Asynchronous event publishing with error tolerance
- **Input Validation**: Comprehensive validation for all API inputs
- **Date Handling**: Consistent ISO format usage across all date fields
- **Communication Tracking**: Automatic last contact date updates
- **Security**: No sensitive data logging, proper error message sanitization