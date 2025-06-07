# Matching Service - Bundle System Implementation

## Overview
The Matching Service has been completely redesigned to implement the bundle-based matching system. The old placement request system has been fully removed in favor of a more sophisticated bundle approach that handles parallel searches and cooling periods.

## Current Status
- ✅ Database schema complete with German field names
- ✅ PlacementRequest table and all references removed from database
- ✅ Bundle system tables created (platzsuche, therapeutenanfrage, therapeut_anfrage_patient)
- ✅ PlacementRequest model and code completely removed
- ✅ Bundle models created with full relationships and business logic
- ✅ Bundle algorithm fully implemented
- 🟡 API endpoints partially functional (algorithm works, need connection)
- 🔄 Integration with email sending needs implementation

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

## API Endpoints (🟡 PARTIALLY FUNCTIONAL)

**CURRENT STATE**: API endpoints are implemented but need connection to the algorithm. The `/api/buendel/erstellen` endpoint now works with the algorithm.

### Working Endpoints

#### POST /api/buendel/erstellen
Triggers bundle creation for all eligible therapists
```json
{
  "send_immediately": false,
  "dry_run": false
}
```

### Endpoints Needing Integration

#### Patient Search Management

##### POST /api/platzsuchen
Create a new patient search

##### GET /api/platzsuchen/{id}
Get search details with bundle history

##### POST /api/platzsuchen/{id}/kontaktanfrage
Request additional contacts

### Bundle Operations

##### GET /api/therapeutenanfragen/{id}
Get bundle details with patient list

##### PUT /api/therapeutenanfragen/{id}/antwort
Record therapist response

### Analytics Endpoints

##### GET /api/analytics/bundle-efficiency
Bundle performance metrics

##### GET /api/analytics/therapist-preferences
Learned therapist preferences

## Event Management

### Published Events (Publishers Created)

The event publishers have been created and are used by the algorithm:

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

Event consumers are temporarily disabled pending full implementation:
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

### Manual Overrides 🔄
```python
def manual_assignment(patient_id, therapist_id, reason):
    """Allow staff to manually assign patients."""
    # To be implemented with API endpoints
```

## Testing Approach

### Current Testing
- ✅ Service starts without errors
- ✅ Bundle algorithm fully implemented
- ✅ Test script available: `test_bundle_algorithm.py`
- 🔄 API endpoints need integration testing

### Testing the Algorithm
```bash
# Test bundle creation algorithm
cd matching_service
python tests/test_bundle_algorithm.py

# This will:
# 1. Test hard constraints
# 2. Test progressive filtering
# 3. Test bundle composition
# 4. Display scoring details
```

## Current Database State vs Code State

| Component | Database | Models | Algorithm | APIs | Status |
|-----------|----------|--------|-----------|------|--------|
| Patient Fields | German ✅ | German ✅ | Works ✅ | German ✅ | ✅ Working |
| Therapist Fields | German ✅ | German ✅ | Works ✅ | German ✅ | ✅ Working |
| Communication Fields | German ✅ | German ✅ | N/A | German ✅ | ✅ Working |
| PlacementRequest | Removed ✅ | Removed ✅ | N/A | 501 Response ✅ | ✅ Complete |
| Bundle System | Created ✅ | Full ✅ | Implemented ✅ | Partial 🟡 | 🟡 Integration Needed |

## Next Implementation Steps

### Phase 1: Complete API Integration (Current)
1. 🔄 Connect all API endpoints to algorithm
2. 🔄 Implement email sending integration
3. 🔄 Add response handling
4. 🔄 Test full flow

### Phase 2: Event Processing
1. ❌ Re-enable event consumers
2. ❌ Implement event handlers
3. ❌ Test event flow
4. ❌ Add event monitoring

### Phase 3: Testing & Optimization
1. ❌ Integration testing
2. ❌ Performance testing
3. ❌ Edge case handling
4. ❌ Production readiness

## How to Test Current State

```bash
# Test algorithm directly
cd matching_service
python tests/test_bundle_algorithm.py

# Test API endpoints
curl -X POST http://localhost:8003/api/buendel/erstellen \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# Other endpoints still need integration
curl http://localhost:8003/api/platzsuchen  # Still returns 501
```

## Development Notes

### Algorithm Implementation Details
The bundle algorithm uses:
1. **Weighted scoring system** for patient-therapist matching
2. **Hard constraints** that must be satisfied (distance, exclusions, gender)
3. **Progressive filtering** with configurable weights
4. **Conflict resolution** based on first-responder principle
5. **Analytics functions** for monitoring performance

### Current Service Behavior
- Service starts successfully
- Bundle creation algorithm works
- API endpoints partially functional
- Need to connect algorithm to communication service
- Ready for integration work

### For Developers
When completing the integration:
1. Use the implemented `create_bundles_for_all_therapists()` function
2. Connect to `BundleService.send_bundle()` for email creation
3. Handle responses through `BundleService.handle_bundle_response()`
4. Update cooling periods with `TherapistService.set_cooling_period()`
5. Test with the provided test script