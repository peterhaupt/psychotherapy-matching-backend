# Matching Service - Bundle System Implementation

> **Note**: For API endpoint documentation, see `API_REFERENCE.md` which contains the complete API specification.

## Overview
The Matching Service has been completely redesigned to implement the bundle-based matching system. The old placement request system has been fully removed in favor of a more sophisticated bundle approach that handles parallel searches and cooling periods.

## Current Status
- ✅ Database schema complete with German field names
- ✅ PlacementRequest table and all references removed from database
- ✅ Bundle system tables created (platzsuche, therapeutenanfrage, therapeut_anfrage_patient)
- ✅ PlacementRequest model and code completely removed
- ✅ Bundle models created with full relationships and business logic
- ✅ Bundle algorithm fully implemented
- ✅ API endpoints fully functional and integrated
- ✅ Integration with email sending implemented

## Bundle System Architecture

### Core Concepts

1. **Platzsuche (Patient Search)**
   - Represents a patient's ongoing search for therapy
   - Tracks excluded therapists
   - Records total contact attempts
   - Maintains search status

2. **Therapeutenanfrage (Therapist Inquiry)**
   - A bundle of 3-6 patients sent to one therapist
   - Tracks response type and outcomes
   - Records bundle composition

3. **Therapeut Anfrage Patient (Bundle Composition)**
   - Links patients to specific bundles
   - Tracks individual patient outcomes within bundle
   - Maintains position in bundle for prioritization

## Database Schema (✅ COMPLETED)

### platzsuche (Patient Search)
```sql
CREATE TABLE matching_service.platzsuche (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patient_service.patients(id),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    ausgeschlossene_therapeuten JSONB DEFAULT '[]',
    gesamt_angeforderte_kontakte INTEGER DEFAULT 0,
    erfolgreiche_vermittlung_datum TIMESTAMP,
    notizen TEXT
);
```

### therapeutenanfrage (Therapist Inquiry/Bundle)
```sql
CREATE TABLE matching_service.therapeutenanfrage (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL REFERENCES therapist_service.therapists(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_date TIMESTAMP,
    response_date TIMESTAMP,
    antworttyp VARCHAR(50),
    buendelgroesse INTEGER NOT NULL,
    angenommen_anzahl INTEGER DEFAULT 0,
    abgelehnt_anzahl INTEGER DEFAULT 0,
    keine_antwort_anzahl INTEGER DEFAULT 0,
    notizen TEXT,
    email_id INTEGER REFERENCES communication_service.emails(id),
    phone_call_id INTEGER REFERENCES communication_service.phone_calls(id)
);
```

### therapeut_anfrage_patient (Bundle Composition)
```sql
CREATE TABLE matching_service.therapeut_anfrage_patient (
    id SERIAL PRIMARY KEY,
    therapeutenanfrage_id INTEGER NOT NULL REFERENCES therapeutenanfrage(id),
    platzsuche_id INTEGER NOT NULL REFERENCES platzsuche(id),
    patient_id INTEGER NOT NULL REFERENCES patient_service.patients(id),
    position_im_buendel INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    antwortergebnis VARCHAR(50),
    antwortnotizen TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(therapeutenanfrage_id, platzsuche_id)
);
```

## Models (✅ FULL IMPLEMENTATION)

### Implemented Models:
1. ✅ `matching_service/models/platzsuche.py` - Full implementation with business logic
2. ✅ `matching_service/models/therapeutenanfrage.py` - Full implementation with relationships
3. ✅ `matching_service/models/therapeut_anfrage_patient.py` - Full implementation with outcome tracking
4. ✅ All imports updated throughout the codebase
5. ✅ PlacementRequest completely removed from codebase

### Model Features:
- Full relationships between models
- Business logic methods for state transitions
- Validation for status changes
- Helper methods for bundle operations

## Bundle Algorithm Implementation (✅ COMPLETED)

### Overview
The bundle algorithm creates optimal groups of 3-6 patients for each contactable therapist using progressive filtering. The algorithm is implemented in `matching_service/algorithms/bundle_creator.py`.

### Algorithm Steps

```python
def create_bundles_for_all_therapists():
    """Create bundles for all eligible therapists."""
    
    # Step 1: Get contactable therapists
    therapists = get_contactable_therapists()  # Not in cooling period
    
    # Step 2: Get active patient searches
    patient_searches = get_active_patient_searches()
    
    # Step 3: Create bundles
    for therapist in therapists:
        # Apply hard constraints
        eligible_patients = apply_hard_constraints(
            therapist, patient_searches
        )
        
        # Apply progressive filtering
        filtered_patients = apply_progressive_filtering(
            therapist, eligible_patients
        )
        
        # Select top patients by wait time
        bundle_patients = select_bundle_patients(
            filtered_patients, 
            min_size=3, 
            max_size=6
        )
        
        if len(bundle_patients) >= 3:
            create_bundle(therapist, bundle_patients)
```

### Hard Constraints (MUST be satisfied)
```python
def apply_hard_constraints(therapist, patient_searches):
    eligible = []
    for search in patient_searches:
        patient = get_patient(search.patient_id)
        
        # Distance check
        distance = calculate_distance(patient, therapist)
        if distance > patient.max_travel_distance:
            continue
            
        # Exclusion check
        if therapist.id in search.ausgeschlossene_therapeuten:
            continue
            
        # Gender preference check (patient's preference)
        if not matches_gender_preference(therapist, patient):
            continue
            
        eligible.append(search)
    return eligible
```

### Progressive Filtering with Scoring System
The algorithm uses a weighted scoring system to rank patient-therapist compatibility:

```python
def calculate_patient_score(therapist, patient, search):
    """Calculate compatibility score (0-100)."""
    score = 0.0
    
    # 1. Availability compatibility (40% weight)
    availability_score = score_by_availability(
        patient.zeitliche_verfuegbarkeit,
        therapist.arbeitszeiten
    )
    score += availability_score * 40
    
    # 2. Diagnosis preference (30% weight)
    diagnosis_score = score_by_therapist_preferences(
        patient, therapist
    )
    score += diagnosis_score * 30
    
    # 3. Age preference (20% weight)
    age_score = score_by_age_preference(
        patient.geburtsdatum,
        therapist.alter_min,
        therapist.alter_max
    )
    score += age_score * 20
    
    # 4. Group therapy compatibility (10% weight)
    group_score = score_by_group_therapy(
        patient.offen_fuer_gruppentherapie,
        therapist.bevorzugt_gruppentherapie
    )
    score += group_score * 10
    
    return score
```

### Conflict Resolution
```python
def resolve_conflicts(conflicts):
    """Handle when patient is accepted by multiple therapists.
    First therapist to respond gets the patient."""
    
    resolutions = {}
    for conflict in conflicts:
        # Get bundles and sort by response date
        bundles = get_bundles_for_therapists(conflict['therapist_ids'])
        bundles.sort(key=lambda b: b.response_date)
        
        # First responder wins
        winning_therapist_id = bundles[0].therapist_id
        resolutions[conflict['patient_id']] = winning_therapist_id
    
    return resolutions
```

## Event Management

### Published Events (✅ All Publishers Implemented)

The event publishers have been created and are actively used:

#### bundle.created
```python
publish_bundle_created(bundle_id, therapist_id, patient_ids, bundle_size)
```

#### bundle.sent
```python
publish_bundle_sent(bundle_id, communication_type, communication_id)
```

#### bundle.response_received
```python
publish_bundle_response_received(bundle_id, response_type, accepted_count, rejected_count, no_response_count)
```

#### search.status_changed
```python
publish_search_status_changed(search_id, patient_id, old_status, new_status)
```

#### cooling.period_started
```python
publish_cooling_period_started(therapist_id, next_contactable_date, reason)
```

### Consumed Events

Event consumers are ready but temporarily disabled pending full system integration:
- `patient.deleted`: Will deactivate associated searches
- `therapist.blocked`: Will cancel pending bundles
- `communication.email_sent`: Will update bundle sent timestamp
- `communication.response_received`: Will process therapist response

## Business Rules Implementation

### Cooling Period (Abkühlungsphase) ✅
```python
def set_cooling_period(therapist_id, weeks=4):
    """Set cooling period after any contact."""
    next_contact = datetime.utcnow() + timedelta(weeks=weeks)
    # Updates therapist.naechster_kontakt_moeglich
```

### Conflict Resolution ✅
```python
def resolve_conflicts(accepted_bundles):
    """Handle when patient is accepted by multiple therapists."""
    # First to respond wins
    # Others notified of conflict
```

### Email Integration ✅
The service now creates professional HTML emails for bundles:
- Patient information formatted in a clear list
- Reference number for tracking
- Professional styling
- Both HTML and plain text versions

## Current Database State vs Code State

| Component | Database | Models | Algorithm | APIs | Status |
|-----------|----------|--------|-----------|------|--------|
| Patient Fields | German ✅ | German ✅ | Works ✅ | German ✅ | ✅ Working |
| Therapist Fields | German ✅ | German ✅ | Works ✅ | German ✅ | ✅ Working |
| Communication Fields | German ✅ | German ✅ | N/A | German ✅ | ✅ Working |
| PlacementRequest | Removed ✅ | Removed ✅ | N/A | 501 Response ✅ | ✅ Complete |
| Bundle System | Created ✅ | Full ✅ | Implemented ✅ | Functional ✅ | ✅ Complete |

## Technical Details for Developers

The implementation includes:
- **520+ lines** of fully functional API code
- **Complete service integration** layer
- **Professional email templates** with HTML formatting
- **Comprehensive error handling** and logging
- **Event-driven architecture** with Kafka integration
- **Full CRUD operations** for all bundle entities
- **Pagination support** on all collection endpoints
- **Advanced filtering** capabilities
- **Robust validation** with meaningful error messages

All code follows the established patterns:
- German field names throughout
- Centralized configuration usage
- Proper separation of concerns
- RESTful design principles
- Comprehensive documentation

## Integration with Other Services

### Communication Service Integration ✅
- Creates emails through Communication Service API
- Uses German field names in requests
- Tracks email_id in bundle records
- Schedules follow-up calls when needed

### Patient/Therapist Service Integration ✅
- Fetches data via REST APIs
- Handles missing data gracefully
- Caches responses where appropriate

### Geocoding Service Integration ✅
- Calculates distances for hard constraints
- Uses travel mode preferences
- Handles calculation failures gracefully

## Next Steps

The system is now ready for:
- ✅ Integration testing
- ✅ Performance testing with large datasets
- ✅ Frontend integration
- 🔄 Production deployment preparation
- 🔄 Event consumer re-enablement
- 🔄 Monitoring and alerting setup

## Performance Considerations

The implementation handles:
- Efficient database queries with proper indexing
- Batch processing for bundle creation
- Connection pooling for cross-service calls
- Graceful degradation when services unavailable
- Configurable timeouts and retries