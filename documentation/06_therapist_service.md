# Therapist Service

> **Note**: For complete API documentation, see `API_REFERENCE.md`

## Summary
Core microservice handling all therapist-related data and operations for the Psychotherapy Matching Platform. Manages therapist profiles, availability tracking, preference management, and status control with full German field naming consistency.

## Models Implementation

### Therapist Model (`therapist_service/models/therapist.py`)
Comprehensive therapist data model with German field names:
- **Personal information**: `anrede`, `titel`, `vorname`, `nachname`, contact details
- **Professional details**: `kassensitz`, `psychotherapieverfahren`, `zusatzqualifikationen`
- **Availability data**: `telefonische_erreichbarkeit`, `arbeitszeiten` (JSONB format)
- **Contact history**: `letzter_kontakt_email`, `letzter_kontakt_telefon`
- **Anfrage preferences**: `bevorzugte_diagnosen`, `alter_min`/`alter_max`, `geschlechtspraeferenz`

### Status Management
The `TherapistStatus` enum defines therapist operational states:
- **AKTIV**: Available for new patient inquiries
- **GESPERRT**: Temporarily blocked from receiving new matches
- **INAKTIV**: No longer active in the system

### Availability Tracking
Advanced availability management system:
- **Phone availability**: Structured time slots for different weekdays
- **Working hours**: Professional schedule management
- **Cooling periods**: Automatic contact spacing via `naechster_kontakt_moeglich`
- **Capacity management**: `potenziell_verfuegbar` flag with notes

## Key Features

### Professional Information Management
- **Therapy methods**: Support for multiple `psychotherapieverfahren`
- **Languages**: `fremdsprachen` support for international patients
- **Qualifications**: `zusatzqualifikationen` and `besondere_leistungsangebote`
- **Insurance**: `kassensitz` status for coverage verification

### Contact History Tracking
- **Email contacts**: `letzter_kontakt_email` with automatic updates
- **Phone contacts**: `letzter_kontakt_telefon` with automatic updates
- **Personal meetings**: `letztes_persoenliches_gespraech` tracking
- **Communication integration**: Automatic updates when communications sent

### Anfrage System Integration
- **Patient preferences**: Age range and gender preferences for patients
- **Diagnosis specialization**: `bevorzugte_diagnosen` array for matching
- **Therapy approach**: Group vs. individual therapy preferences
- **Geographic service area**: PLZ-based service area definition

## Business Logic

### Cooling Period Management
Automatic contact frequency control:
- **Default period**: 4 weeks between inquiries
- **Automatic setting**: Updates `naechster_kontakt_moeglich` after responses
- **Manual override**: Administrative control for special cases
- **Bypass conditions**: Emergency or high-priority patient matching

### Status Transitions
Controlled therapist status management:
- **Blocking**: Automatic or manual status change to `gesperrt`
- **Reason tracking**: `sperrgrund` and `sperrdatum` for audit trail
- **Event publishing**: Status changes trigger system-wide notifications
- **Reactivation**: Controlled process for returning blocked therapists to active status

### Preference Matching
Sophisticated preference management for anfrage composition:
- **Hard constraints**: All preferences must be satisfied or null
- **Flexible matching**: Null preferences act as wildcards
- **Priority weighting**: Available and informed therapists prioritized
- **Geographic clustering**: PLZ-based therapist selection

## Event Management

### Event Publishers (`events/producers.py`)
Comprehensive Kafka event system:
- `therapist.created` - New therapist registration
- `therapist.updated` - Profile or preference changes
- `therapist.blocked` - Status change to blocked with reason
- `therapist.unblocked` - Reactivation from blocked status

### Event Consumers (`events/consumers.py`)
Framework for processing events from other services:
- **Patient events**: React to patient creation/updates for matching optimization
- **Communication events**: Process email responses and call outcomes
- **Matching events**: Handle anfrage responses and conflicts

## Integration Points

### With Communication Service
- **Email management**: Send inquiries and follow-up communications
- **Phone scheduling**: Automatic scheduling based on `telefonische_erreichbarkeit`
- **Response tracking**: Monitor inquiry responses and outcomes
- **History aggregation**: Combined communication timeline

### With Matching Service
- **Availability queries**: Real-time therapist availability checking
- **Preference filtering**: Apply therapist constraints in anfrage creation
- **Cooling period enforcement**: Respect contact frequency limits
- **Response processing**: Handle anfrage outcomes and update status

### With Patient Service
- **Cross-referencing**: Validate patient-therapist compatibility
- **Exclusion management**: Maintain therapist exclusion lists
- **Preference matching**: Apply mutual preference constraints

## Communication Utilities (`therapist_service/utils/communication.py`)
Helper functions for therapist communication:
- `send_therapist_email()`: Send emails with automatic contact date updates
- `schedule_therapist_call()`: Schedule calls with availability checking
- **Markdown support**: Rich email formatting with automatic link detection
- **Legal compliance**: Automatic footer inclusion for regulatory compliance

## Configuration Integration

### Centralized Settings
All configuration managed through `shared.config`:
- **Database connectivity**: PgBouncer connection pooling
- **Service communication**: Internal API endpoints
- **Kafka messaging**: Event streaming configuration
- **Email settings**: SMTP and template configuration

### Feature Flags
- **Anfrage system**: Enable/disable new matching features
- **Communication**: Control email and phone call functionality
- **Data validation**: Toggle strict validation rules

## Security and Compliance

### Data Protection
- **Contact information**: Secure handling of personal contact details
- **Professional credentials**: Protected storage of qualification data
- **Communication history**: Encrypted storage of sensitive interactions
- **Access control**: Role-based access to therapist information

### Audit Trail
- **Status changes**: Complete history of therapist status modifications
- **Contact tracking**: Detailed log of all communication attempts
- **Preference updates**: Audit trail for matching preference changes
- **System events**: Comprehensive event logging for compliance

## Performance Optimizations

### Database Design
- **Indexed fields**: Optimized queries for status and availability
- **JSONB usage**: Efficient storage and querying of complex preferences
- **Connection pooling**: Shared database connections via PgBouncer
- **Query optimization**: Minimized cross-service API calls

### Caching Strategy
- **Availability checks**: Cached therapist availability data
- **Preference queries**: Optimized matching constraint evaluation
- **Status updates**: Efficient propagation of status changes

This service forms the backbone of therapist management in the platform, providing comprehensive professional profile management while maintaining strict data consistency and integration with the broader matching ecosystem.