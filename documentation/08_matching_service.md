# Matching Service - Bundle System Implementation

## Overview
The Matching Service has been completely redesigned to implement the bundle-based matching system. The old placement request system has been removed entirely in favor of a more sophisticated bundle approach that handles parallel searches and cooling periods.

## Current Status
- ✅ Database schema complete with German field names
- ✅ PlacementRequest table and references removed from database
- ✅ Bundle system tables created (platzsuche, therapeutenanfrage, therapeut_anfrage_patient)
- ❌ Model implementation needed (PlacementRequest still exists in code)
- ❌ API endpoints need updating (old endpoints still present)
- ❌ Bundle algorithm needs implementation

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

## Models (❌ To Be Implemented)

**CURRENT STATE**: The codebase still contains the old PlacementRequest model and needs to be updated.

### Required Actions:
1. Delete `matching_service/models/placement_request.py`
2. Create `matching_service/models/platzsuche.py`
3. Create `matching_service/models/therapeutenanfrage.py`
4. Create `matching_service/models/therapeut_anfrage_patient.py`
5. Update all imports throughout the codebase
6. Remove PlacementRequest from `migrations/alembic/env.py`

## Bundle Algorithm Implementation

### Overview
The bundle algorithm creates optimal groups of 3-6 patients for each contactable therapist using progressive filtering.

### Algorithm Steps

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

## API Endpoints (❌ To Be Implemented)

**CURRENT STATE**: The API still uses the old placement request endpoints.

### Required Actions:
1. Remove all `/api/placement-requests` endpoints
2. Implement new bundle system endpoints

### Patient Search Management

#### POST /api/platzsuchen
Create a new patient search:
```json
{
  "patient_id": 123,
  "notizen": "Patient very motivated"
}
```

#### GET /api/platzsuchen/{id}
Get search details with bundle history

#### POST /api/platzsuchen/{id}/kontaktanfrage
Request additional contacts:
```json
{
  "anzahl": 25,
  "notizen": "Patient requests more options"
}
```

### Bundle Operations

#### POST /api/buendel/erstellen
Trigger bundle creation for all eligible therapists

#### GET /api/therapeutenanfragen/{id}
Get bundle details with patient list

#### PUT /api/therapeutenanfragen/{id}/antwort
Record therapist response:
```json
{
  "antworttyp": "teilweise_angenommen",
  "patient_antworten": [
    {"patient_id": 1, "ergebnis": "angenommen"},
    {"patient_id": 2, "ergebnis": "abgelehnt", "grund": "Keine Kapazität"},
    {"patient_id": 3, "ergebnis": "angenommen"}
  ]
}
```

### Analytics Endpoints

#### GET /api/analytics/bundle-efficiency
Bundle performance metrics

#### GET /api/analytics/therapist-preferences
Learned therapist preferences

## Event Management

### Published Events

#### bundle.created
```json
{
  "eventType": "bundle.created",
  "payload": {
    "bundle_id": 123,
    "therapist_id": 456,
    "patient_ids": [1, 2, 3, 4, 5],
    "bundle_size": 5
  }
}
```

#### bundle.response_received
```json
{
  "eventType": "bundle.response_received",
  "payload": {
    "bundle_id": 123,
    "response_type": "teilweise_angenommen",
    "accepted_count": 2,
    "rejected_count": 3
  }
}
```

#### search.status_changed
```json
{
  "eventType": "search.status_changed",
  "payload": {
    "search_id": 789,
    "old_status": "active",
    "new_status": "successful"
  }
}
```

### Consumed Events

- `patient.deleted`: Deactivate associated searches
- `therapist.blocked`: Cancel pending bundles
- `communication.email_sent`: Update bundle sent timestamp
- `communication.response_received`: Process therapist response

## Business Rules Implementation

### Cooling Period (Abkühlungsphase)
```python
def set_cooling_period(therapist_id, weeks=4):
    """Set cooling period after any contact."""
    therapist = get_therapist(therapist_id)
    therapist.naechster_kontakt_moeglich = (
        date.today() + timedelta(weeks=weeks)
    )
```

### Conflict Resolution
```python
def resolve_conflicts(accepted_bundles):
    """Handle when patient is accepted by multiple therapists."""
    # First acceptance wins
    # Notify other therapists immediately
    # Offer alternative patients from their bundles
```

### Manual Overrides
```python
def manual_assignment(patient_id, therapist_id, reason):
    """Allow staff to manually assign patients."""
    # Create special bundle entry
    # Document reason
    # May override cooling period
```

## Testing Approach

### Unit Tests
- Bundle creation logic
- Progressive filtering
- Cooling period calculations
- Conflict resolution

### Integration Tests
- Full bundle flow
- Event publishing/consumption
- API endpoint testing
- Database constraint validation

### Performance Tests
- Bundle creation with 100+ patients
- Concurrent bundle processing
- Query optimization verification

## Migration from PlacementRequest

### Database Changes (✅ COMPLETED)
1. **Removed**: placement_requests table
2. **Added**: Bundle system tables (platzsuche, therapeutenanfrage, etc.)
3. **Updated**: Foreign key references in communication service
4. **Applied**: All migrations successfully

### Code Changes (❌ PENDING)
1. Remove models/placement_request.py
2. Remove PlacementRequest from models/__init__.py
3. Remove PlacementRequest API endpoints
4. Remove PlacementRequest events
5. Update imports throughout
6. Remove from alembic env.py

## Next Implementation Steps

1. **Create Model Files**
   - platzsuche.py
   - therapeutenanfrage.py
   - therapeut_anfrage_patient.py

2. **Implement Bundle Algorithm**
   - bundle_creator.py
   - progressive_filter.py
   - conflict_resolver.py

3. **Create API Endpoints**
   - Remove old matching.py
   - Create bundle_api.py
   - Create search_api.py

4. **Update Event Handling**
   - Remove placement events
   - Add bundle events
   - Update consumers

5. **Write Tests**
   - Test bundle creation
   - Test API endpoints
   - Test event flow