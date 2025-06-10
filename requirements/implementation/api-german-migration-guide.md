# API German Field Names Migration Guide

## Overview
This guide provides step-by-step instructions to migrate all API field names to German, while keeping system/wrapper fields in English. The migration is designed to be executed in phases across multiple chat sessions.

## Migration Principles
1. **English remains for**: System fields (`id`, `created_at`, `updated_at`) and API wrapper fields (`data`, `message`, `error`, `page`, `limit`, `total`)
2. **German for everything else**: All business data, enum values, calculated fields
3. **Database priority**: When a database field exists, use that exact German name

## Phase 1: Database Enum Value Migration

### Objective
Update all enum values in the database from English to German.

### Affected Enums
1. **EmailStatus** (already English: DRAFT, QUEUED, SENDING, SENT, FAILED) - No change needed
2. **Search Status** - Need to create migration for:
   - `active` → `aktiv`
   - `successful` → `erfolgreich`
   - `paused` → `pausiert`
   - `cancelled` → `abgebrochen`
3. **Phone Call Status** - Update to German:
   - `scheduled` → `geplant`
   - `completed` → `abgeschlossen`
   - `failed` → `fehlgeschlagen`
   - `canceled` → `abgebrochen`

### Steps
1. Create new Alembic migration: `alembic revision -m "update_enum_values_to_german"`
2. Update the enums in the migration file
3. Run migration: `alembic upgrade head`
4. Verify enum values in database

### SQL to Check Current Enums
```sql
SELECT n.nspname as enum_schema,  
       t.typname as enum_name,  
       array_agg(e.enumlabel ORDER BY e.enumsortorder) as values
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid  
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
GROUP BY n.nspname, t.typname
ORDER BY enum_name;
```

## Phase 2: Model Updates

### Objective
Update all model enum definitions to use German values.

### Affected Files
1. **matching_service/models/platzsuche.py** - Update search status enum
2. **communication_service/models/phone_call.py** - Update phone call status values
3. Any other models using these enums

### Example Changes
```python
# Before
class SearchStatus(str, Enum):
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    PAUSED = "paused"
    CANCELLED = "cancelled"

# After
class SearchStatus(str, Enum):
    ACTIVE = "aktiv"
    SUCCESSFUL = "erfolgreich"
    PAUSED = "pausiert"
    CANCELLED = "abgebrochen"
```

## Phase 3: API Response Field Updates - Matching Service

### Objective
Fix all inconsistent field names in the Matching Service API responses.

### Files to Update
1. **matching_service/api/platzsuchen.py**
2. **matching_service/api/therapeutenanfragen.py**
3. **matching_service/api/bundle_operations.py**

### Field Mappings
```python
# List response fields
'excluded_therapists_count' → 'ausgeschlossene_therapeuten_anzahl'
'active_bundles' → 'aktive_buendel'
'total_bundles' → 'gesamt_buendel'
'patient_name' → 'patienten_name'

# Detail response fields
'bundle_history' → 'buendel_verlauf'
'days_since_sent' → 'tage_seit_versand'
'response_summary' → 'antwort_zusammenfassung'
'response_complete' → 'antwort_vollstaendig'
'needs_follow_up' → 'nachverfolgung_erforderlich'
'wait_time_days' → 'wartezeit_tage'

# Bundle operation responses
'bundles_created' → 'buendel_erstellt'
'bundles_sent' → 'buendel_gesendet'
'bundle_ids' → 'buendel_ids'
'accepted_patients' → 'angenommene_patienten'

# Request parameters
'send_immediately' → 'sofort_senden'
'dry_run' → 'testlauf'
'sent_status' → 'versand_status'
'response_status' → 'antwort_status'
```

### Example API Response Update
```python
# Before
return {
    "data": [{
        "id": 1,
        "patient_name": "Anna Müller",
        "active_bundles": 3,
        "excluded_therapists_count": 2
    }]
}

# After
return {
    "data": [{
        "id": 1,
        "patienten_name": "Anna Müller",
        "aktive_buendel": 3,
        "ausgeschlossene_therapeuten_anzahl": 2
    }]
}
```

## Phase 4: API Response Field Updates - Other Services

### Communication Service
Update any calculated fields in email/phone call responses:
- Verify all fields already use German names from database

### Geocoding Service
Keep as-is (technical fields remain in English by design)

### Patient/Therapist Services
Verify all response fields match database field names

## Phase 5: API Documentation Update

### Objective
Update API_REFERENCE.md to reflect all German field names.

### Steps
1. Update all example requests and responses
2. Update field descriptions
3. Update enum value examples
4. Ensure consistency across all endpoints

### Documentation Sections to Update
1. Enum Values section
2. All example responses
3. Query parameter names
4. Request body field names

## Phase 6: Integration Testing

### Test Checklist
1. **Create operations**: Test creating entities with German field names
2. **List operations**: Verify German field names in list responses
3. **Detail operations**: Check German field names in detail responses
4. **Filter operations**: Test query parameters with German names
5. **Bundle operations**: Verify all bundle-related German fields

### Test Commands
```bash
# Test patient search list
curl "http://localhost:8003/api/platzsuchen"

# Test bundle creation
curl -X POST "http://localhost:8003/api/buendel/erstellen" \
  -H "Content-Type: application/json" \
  -d '{"sofort_senden": false, "testlauf": false}'

# Test therapist inquiry with filters
curl "http://localhost:8003/api/therapeutenanfragen?versand_status=gesendet"
```

## Verification Checklist

### Phase 1 Complete When:
- [ ] All enum values in database are German
- [ ] No English enum values remain (except EmailStatus which is already correct)

### Phase 2 Complete When:
- [ ] All model files use German enum values
- [ ] No English enum values in Python code

### Phase 3 Complete When:
- [ ] All Matching Service API responses use German field names
- [ ] No duplicate concepts (English/German for same data)
- [ ] All calculated fields are German

### Phase 4 Complete When:
- [ ] All services return consistent German field names
- [ ] Only system/wrapper fields remain in English

### Phase 5 Complete When:
- [ ] API documentation matches actual API responses
- [ ] All examples use German field names
- [ ] Enum values documentation is updated

### Phase 6 Complete When:
- [ ] All API endpoints tested
- [ ] No English business fields in any response
- [ ] Frontend can consume API without field name issues

## Common Pitfalls to Avoid

1. **Don't translate system fields**: Keep `id`, `created_at`, `updated_at`
2. **Don't translate wrapper fields**: Keep `data`, `message`, `error`, `page`, `limit`, `total`
3. **Match database exactly**: If database has `keine_antwort_anzahl`, don't use `kein_antwort_anzahl`
4. **Consistent compounds**: Use underscores consistently in compound words
5. **Test after each phase**: Don't wait until the end to test

## Notes for Implementation

- Each phase can be done independently in a separate chat session
- Always verify current state before making changes
- Use the terminology document as the source of truth for translations
- Test each service after its updates before moving to the next