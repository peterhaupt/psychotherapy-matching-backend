# Matching Service - Bundle System Implementation

## Overview
The Matching Service has been completely redesigned to implement the bundle-based matching system. The old placement request system has been fully removed in favor of a more sophisticated bundle approach that handles parallel searches and cooling periods.

## Current Status
- ✅ Database schema complete with German field names
- ✅ PlacementRequest table and all references removed from database
- ✅ Bundle system tables created (platzsuche, therapeutenanfrage, therapeut_anfrage_patient)
- ✅ PlacementRequest model and code completely removed
- ✅ Stub bundle models created (basic structure only)
- 🟡 API endpoints return 501 (Not Implemented) - no crashes
- ❌ Bundle algorithm needs full implementation
- ❌ API endpoints need actual implementation

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

## Models (🟡 STUB IMPLEMENTATION)

**CURRENT STATE**: Basic stub models exist to prevent import errors.

### Implemented Stubs:
1. ✅ `matching_service/models/platzsuche.py` - Basic structure
2. ✅ `matching_service/models/therapeutenanfrage.py` - Basic structure
3. ✅ `matching_service/models/therapeut_anfrage_patient.py` - Basic structure
4. ✅ All imports updated throughout the codebase
5. ✅ PlacementRequest completely removed from codebase

### Still Needed:
- Full model implementation with relationships
- Model methods for bundle operations
- Validation logic

## Bundle Algorithm Implementation

### Overview
The bundle algorithm creates optimal groups of 3-6 patients for each contactable therapist using progressive filtering.

### Algorithm Steps (NOT YET IMPLEMENTED)

```python
def erstelle_buendel_fuer_alle_therapeuten():
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

### Progressive Filtering
```python
def apply_progressive_filtering(therapist, patients):
    """Apply soft preferences progressively."""
    
    # Level 1: Availability compatibility
    if therapist.arbeitszeiten:
        patients = filter_by_availability(patients, therapist)
    
    # Level 2: Therapist preferences
    patients = score_by_preferences(patients, therapist)
    
    # Level 3: Sort by wait time (longest first)
    patients.sort(key=lambda p: p.created_at)
    
    return patients
```

## API Endpoints (🟡 STUB IMPLEMENTATION)

**CURRENT STATE**: All API endpoints return 501 (Not Implemented) with a message explaining the bundle system is in development. No crashes or database errors occur.

### Temporary Stub Endpoints

#### GET /api/placement-requests
Returns:
```json
{
  "message": "Bundle system not yet implemented",
  "data": [],
  "page": 1,
  "limit": 20,
  "total": 0
}
```
Status: 501

#### POST /api/placement-requests
#### GET /api/placement-requests/{id}
#### PUT /api/placement-requests/{id}
#### DELETE /api/placement-requests/{id}
All return:
```json
{
  "message": "Bundle system not yet implemented"
}
```
Status: 501

### Planned Bundle System Endpoints (NOT YET IMPLEMENTED)

#### Patient Search Management

##### POST /api/platzsuchen
Create a new patient search

##### GET /api/platzsuchen/{id}
Get search details with bundle history

##### POST /api/platzsuchen/{id}/kontaktanfrage
Request additional contacts

### Bundle Operations

##### POST /api/buendel/erstellen
Trigger bundle creation for all eligible therapists

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

### Published Events (Stubs Created)

The event publishers have been created but are not yet used:

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

## Business Rules Implementation (PLANNED)

### Cooling Period (Abkühlungsphase)
```python
def set_cooling_period(therapist_id, weeks=4):
    """Set cooling period after any contact."""
    # To be implemented
```

### Conflict Resolution
```python
def resolve_conflicts(accepted_bundles):
    """Handle when patient is accepted by multiple therapists."""
    # To be implemented
```

### Manual Overrides
```python
def manual_assignment(patient_id, therapist_id, reason):
    """Allow staff to manually assign patients."""
    # To be implemented
```

## Testing Approach

### Current Testing
- ✅ Service starts without errors
- ✅ All endpoints return proper 501 responses
- ✅ No database errors or crashes
- ✅ Event publishers created (not yet used)

### Planned Testing
- Bundle creation logic
- Progressive filtering
- Cooling period calculations
- Conflict resolution
- Full integration tests

## Migration from PlacementRequest

### Database Changes (✅ COMPLETED)
1. **Removed**: placement_requests table
2. **Added**: Bundle system tables (platzsuche, therapeutenanfrage, etc.)
3. **Updated**: Foreign key references in communication service
4. **Applied**: All migrations successfully

### Code Changes (✅ COMPLETED)
1. ✅ Removed models/placement_request.py
2. ✅ Removed PlacementRequest from models/__init__.py
3. ✅ Updated all API endpoints to return 501
4. ✅ Removed PlacementRequest events
5. ✅ Updated all imports throughout codebase
6. ✅ Removed from alembic env.py

## Next Implementation Steps

### Phase 1: Complete Model Implementation (Next)
1. Add relationships between models
2. Add model methods for business logic
3. Add validation
4. Write unit tests for models

### Phase 2: Implement Bundle Algorithm
1. Create bundle_creator.py
2. Implement hard constraints
3. Implement progressive filtering
4. Add conflict resolution

### Phase 3: Create Real API Endpoints
1. Replace stub endpoints with real implementation
2. Create bundle management endpoints
3. Add search management endpoints
4. Implement analytics endpoints

### Phase 4: Enable Event Processing
1. Re-enable event consumers
2. Implement event handlers
3. Test event flow
4. Add event monitoring

### Phase 5: Integration Testing
1. Test complete bundle creation flow
2. Test therapist response handling
3. Test cooling period enforcement
4. Performance testing with realistic data

## Development Notes

### Why Stub Implementation?
The stub implementation approach was chosen to:
1. Stabilize the service immediately (no more crashes)
2. Allow other teams to continue development
3. Provide clear indication of work in progress (501 status)
4. Maintain clean separation between old and new systems

### Current Service Behavior
- Service starts successfully
- All endpoints respond without errors
- Clear messaging about implementation status
- No database operations performed
- Ready for incremental development

### For Developers
When implementing the full system:
1. Start with models - complete the stub implementations
2. Implement core algorithm functions
3. Replace stub API endpoints one by one
4. Enable events after core functionality works
5. Add comprehensive error handling throughout