# Implementation Plan - Current Status

## Phase 3: Bundle-Based Matching System 🚧 IN PROGRESS

### Overview
Transform the current basic matching system into the bundle-based system described in business requirements. Database schema is complete with German field names - now updating code to match.

### Week 1: Database Schema Updates ✅ COMPLETED

**Completed Tasks:**
- ✅ Migration `acfc96c9f0g0`: Added bundle system tables
- ✅ Migration `bcfc97d0f1h1`: Renamed therapist fields to German
- ✅ Migration series: Cleaned up schema and added missing fields
- ✅ Migration `fcfc01h4l5l5`: Removed placement_requests completely
- ✅ Migration `gcfc02i5m6m6`: Renamed ALL fields to German
- ✅ All database tests passing

### Week 2: German Field Renaming ✅ COMPLETED

**Database Migrations Applied:**
- ✅ All tables now use German field names
- ✅ Foreign key relationships updated
- ✅ Indexes created with German names
- ✅ Enum types properly configured
- ✅ test_database_schemas.py fully passing

### Week 3: Model & Code Updates 🔄 CURRENT WEEK

#### Day 1-2: Model File Updates 🔄 TODAY'S TASKS

**1. Update Therapist Model** (`therapist_service/models/therapist.py`)
```python
# Change these field definitions:
potentially_available → potenziell_verfuegbar
potentially_available_notes → potenziell_verfuegbar_notizen
next_contactable_date → naechster_kontakt_moeglich
preferred_diagnoses → bevorzugte_diagnosen
age_min → alter_min
age_max → alter_max
gender_preference → geschlechtspraeferenz
working_hours → arbeitszeiten
# Add: bevorzugt_gruppentherapie
```

**2. Update Communication Models**

Email Model (`communication_service/models/email.py`):
```python
subject → betreff
recipient_email → empfaenger_email
recipient_name → empfaenger_name
sender_email → absender_email
sender_name → absender_name
response_received → antwort_erhalten
response_date → antwortdatum
response_content → antwortinhalt
follow_up_required → nachverfolgung_erforderlich
follow_up_notes → nachverfolgung_notizen
error_message → fehlermeldung
retry_count → wiederholungsanzahl
```

PhoneCall Model (`communication_service/models/phone_call.py`):
```python
scheduled_date → geplantes_datum
scheduled_time → geplante_zeit
duration_minutes → dauer_minuten
actual_date → tatsaechliches_datum
actual_time → tatsaechliche_zeit
outcome → ergebnis
notes → notizen
retry_after → wiederholen_nach
```

EmailBatch & PhoneCallBatch:
```python
placement_request_id → therapeut_anfrage_patient_id (+ update foreign key)
response_outcome → antwortergebnis
response_notes → antwortnotizen
follow_up_required → nachverfolgung_erforderlich
follow_up_notes → nachverfolgung_notizen
```

**3. Create Bundle Models** (`matching_service/models/`)
- Create `platzsuche.py`
- Create `therapeutenanfrage.py`
- Create `therapeut_anfrage_patient.py`
- Update `__init__.py` to export new models
- DELETE `placement_request.py`

**4. Update Import References**
- Remove PlacementRequest from `migrations/alembic/env.py`
- Update all service imports
- Update event handling code

#### Day 3-4: API Updates

**1. Update API Field Names**
- Patient API: No changes needed (already German)
- Therapist API: Update field names in responses
- Communication API: Update all field names
- Matching API: Complete rewrite for bundles

**2. Remove PlacementRequest Endpoints**
- Delete old endpoints from `matching_service/api/matching.py`
- Create new bundle endpoints

**3. Update Request Parsing**
- Update all `reqparse` arguments to German names
- Update validation logic

#### Day 5: Event System Updates

**1. Update Event Payloads**
- Use German field names in all events
- Remove placement_request references
- Add bundle event types

**2. Update Consumers**
- Update field access to use German names
- Handle new bundle events

### Week 4: Bundle Algorithm & Testing 📋 PLANNED

#### Day 1-2: Bundle Algorithm
- Implement `bundle_creator.py`
- Implement progressive filtering
- Add cooling period logic
- Create conflict resolution

#### Day 3-4: Integration
- Connect all services
- Test full bundle flow
- Debug issues

#### Day 5: Testing
- Unit tests for algorithm
- API endpoint tests
- Performance testing

## Implementation Checklist

### Immediate Tasks (Today/Tomorrow)

#### Therapist Model Update
- [ ] Open `therapist_service/models/therapist.py`
- [ ] Rename all fields to German
- [ ] Update helper methods to use new names
- [ ] Test model changes

#### Communication Models Update
- [ ] Update Email model fields
- [ ] Update PhoneCall model fields
- [ ] Update Batch models with new FK
- [ ] Update all field references in code

#### Bundle Models Creation
- [ ] Create Platzsuche model
- [ ] Create Therapeutenanfrage model
- [ ] Create TherapeutAnfragePatient model
- [ ] Remove PlacementRequest completely

#### Code Cleanup
- [ ] Remove PlacementRequest imports
- [ ] Update alembic env.py
- [ ] Update all API endpoints
- [ ] Fix event handling

### Testing After Each Change
```bash
# After updating models, test database connection:
docker-compose exec matching_service python -c "from models import *"

# Run schema tests:
python tests/integration/test_database_schemas.py

# Test API endpoints:
curl http://localhost:8002/api/therapists
```

## Critical Path

1. **Models MUST be updated first** - Everything depends on this
2. **Then API endpoints** - So frontend can start adapting
3. **Then bundle algorithm** - Core business logic
4. **Finally extensive testing** - Ensure quality

## Definition of Done for Current Phase

### Models Updated ❌
- [ ] All models use German field names
- [ ] PlacementRequest removed completely
- [ ] Bundle models created
- [ ] All imports updated
- [ ] Models can be imported without errors

### APIs Updated ❌
- [ ] All endpoints use German field names
- [ ] PlacementRequest endpoints removed
- [ ] Bundle endpoints created
- [ ] API documentation updated
- [ ] Postman/curl tests pass

### Bundle System Working ❌
- [ ] Can create patient searches
- [ ] Can create bundles
- [ ] Progressive filtering works
- [ ] Cooling periods enforced
- [ ] Conflicts resolved properly

### Tests Passing ❌
- [ ] Unit tests updated and passing
- [ ] Integration tests for bundles
- [ ] Performance within targets
- [ ] No regression in other services

## Risk Mitigation

### Current Risks
1. **Field name mismatches** - Mitigated by systematic updates
2. **Broken imports** - Test after each file change
3. **API compatibility** - Document all changes clearly
4. **Event system issues** - Update producers and consumers together

### Rollback Plan
- All migrations are reversible
- Git commits after each major change
- Database backups before major updates

## Communication Points

### For Frontend Team
- API field names are changing to German
- PlacementRequest endpoints will stop working
- New bundle endpoints coming soon
- Refer to updated API documentation

### For Testing Team
- Models being updated now
- API changes coming in 2-3 days
- Full bundle system in ~1 week
- Prepare test data with German fields

---
*Current Status: Database complete, starting model updates*
*Next Milestone: All models updated with German fields*
*Target: Bundle system operational by end of week*