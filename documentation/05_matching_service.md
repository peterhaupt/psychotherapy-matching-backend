# Matching Service - Anfrage System ✅ FULLY FUNCTIONAL

> **Note**: For complete API documentation, see `API_REFERENCE.md`

## Summary
FULLY OPERATIONAL anfrage-based matching system that creates optimal groups of 1-6 patients for therapists through manual therapist selection, handles responses, and manages the entire matching workflow.

## Current Status ✅ PRODUCTION READY
- **Database**: Complete schema with German field names
- **Models**: Full implementation with business logic
- **Algorithm**: Manual therapist selection with hard constraints
- **APIs**: All endpoints functional and tested
- **Integration**: Direct synchronous communication with other services

## Core Components

### Database Tables (German names)
1. **platzsuche**: Patient search tracking
2. **therapeutenanfrage**: Anfrage/inquiry to therapist  
3. **therapeut_anfrage_patient**: Anfrage composition

### Models (Full Implementation)
See `models/` directory:
- **Platzsuche**: Tracks search status, exclusions, contact count
- **Therapeutenanfrage**: Anfrage with response tracking
- **TherapeutAnfragePatient**: Individual patient outcomes

### Anfrage Algorithm (`algorithms/anfrage_creator.py`)
```python
# Main workflow
1. Get therapists for selection by PLZ prefix (manual selection)
2. Apply hard constraints (distance, exclusions, gender, preferences)
3. No scoring - ALL constraints must be satisfied or null
4. Select oldest patients first (by search creation date)
5. Create anfrage with 1-6 patients and send via Communication Service
```

## System Architecture

### Manual Therapist Selection
- **PLZ-based filtering**: Two-digit postal code prefix matching
- **Prioritized sorting**: Available + informed, Available + not informed, Not available + informed, Others
- **Contactable check**: Respects cooling periods (`naechster_kontakt_moeglich`)
- **Email deduplication**: Groups therapists by email, returns only practice owners

### Hard Constraints Only
Unlike scoring systems, this uses binary pass/fail constraints:
- **Distance**: Within patient's max travel distance
- **Exclusions**: Therapist not in patient's exclusion list
- **Patient preferences**: ALL must match or be null (gender, therapy method, group therapy)
- **Therapist preferences**: ALL must match or be null (diagnosis, age, gender)

### Anfrage Composition
- **Size**: 1-6 patients (configurable via `MAX_ANFRAGE_SIZE`, `MIN_ANFRAGE_SIZE`)
- **Selection order**: Oldest searches first (FIFO)
- **PLZ filtering**: Patients must match therapist's PLZ prefix

## Business Rules Implementation

### Cooling Period (✅ Working)
- 4-week default after any contact
- Updates `therapist.naechster_kontakt_moeglich`
- Enforced in therapist selection

### Conflict Resolution (✅ Working)
- First responder wins principle
- Automatic detection of multiple acceptances
- Other therapists notified via exclusion lists

### Response Handling (✅ Working)
Patient outcomes tracked individually:
- `angenommen` - Patient accepted
- `abgelehnt_Kapazitaet` - Rejected due to capacity
- `abgelehnt_nicht_geeignet` - Rejected as not suitable
- `abgelehnt_sonstiges` - Rejected for other reasons
- `nicht_erschienen` - Patient didn't show up
- `in_Sitzungen` - Patient in trial sessions

## Service Integration

### Cross-Service Communication (Synchronous APIs)
- **PatientService**: Fetch patient data for anfrage composition
- **TherapistService**: Get therapist availability, set cooling periods
- **CommunicationService**: Create and send anfrage emails
- **GeoCodingService**: Distance calculations for constraints

### Data Consistency
- **Soft References**: Integer foreign keys without database constraints
- **Service Boundaries**: Each service owns its schema completely
- **Error Handling**: Operations fail gracefully when dependent services unavailable
- **Manual Cleanup**: Administrative processes for orphaned data

### Email Generation
Professional HTML emails automatically generated with:
- Patient list with key demographics (age, diagnosis, location)
- Reference number (A{anfrage_id})
- Clear response instructions
- Company branding and legal footer

## Key API Endpoints

All endpoints documented in `API_REFERENCE.md`:

### Patient Search Management
- Patient search creation and tracking
- Contact request handling
- Search status management

### Therapist Selection
- PLZ-based therapist filtering
- Manual selection interface
- Availability and preference checking

### Anfrage Operations
- Manual anfrage creation for selected therapist
- Response recording and processing
- Conflict detection and resolution

## Configuration

All settings managed through `shared.config`:
- **Anfrage size**: Min/max patients per anfrage
- **PLZ matching**: Digit count for geographic filtering  
- **Distance defaults**: Maximum travel distance
- **Cooling periods**: Duration between contacts
- **API timeouts**: Retry and timeout configurations

## Metrics & Analytics
- Anfrage efficiency calculations
- Response rate tracking
- Acceptance statistics
- Wait time analysis
- Conflict detection and resolution tracking

## Production Considerations
- **Database Indexes**: Optimized for status and date queries
- **Connection Pooling**: Efficient cross-service communication
- **Error Recovery**: Graceful handling of service failures
- **Audit Trail**: Complete logging of all operations
- **Performance**: Designed for high-volume patient matching

## Algorithm Differences from Traditional Matching

### No Scoring System
Traditional matching systems use weighted scoring. This system uses binary constraints:
- **Traditional**: Calculate match score (0-100), rank therapists
- **Anfrage System**: Apply hard filters, manual selection from qualified therapists

### Manual Control
- **Human oversight**: Staff manually selects therapist from filtered list
- **Quality assurance**: Reduces automated mismatches
- **Flexibility**: Allows for business logic not captured in algorithms

### Geographic Batching
- **PLZ-based**: Groups patients and therapists by postal code areas
- **Efficiency**: Reduces communication overhead
- **Locality**: Improves match quality through geographic proximity

## Error Handling

### Service Unavailability
- Returns appropriate HTTP status codes (503 for service unavailable)
- Provides clear error messages for dependent services
- Implements retry logic where appropriate

### Data Integrity
- Service isolation prevents cascading failures
- Each service maintains its own data consistency
- Manual administrative cleanup when needed

This approach prioritizes match quality and human oversight over pure automation, resulting in higher success rates and therapist satisfaction.