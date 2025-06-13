# Database Schema - FINAL State

> **Note**: Complete schema in `migrations/alembic/versions/001_initial_setup.py`

## Summary
FINAL production schema with full German naming and patient communication support. All migrations applied, all services operational.

## Key Updates ✅ COMPLETE

### Patient Communication Support
Communication Service tables now support BOTH therapists AND patients:

```sql
-- Emails table with dual recipient support
CREATE TABLE communication_service.emails (
    therapist_id INTEGER,      -- Nullable
    patient_id INTEGER,        -- Nullable (NEW)
    -- Check constraint: exactly one must be set
    CHECK ((therapist_id IS NOT NULL AND patient_id IS NULL) OR 
           (therapist_id IS NULL AND patient_id IS NOT NULL))
);

-- Phone calls with same pattern
CREATE TABLE communication_service.telefonanrufe (
    therapist_id INTEGER,      -- Nullable  
    patient_id INTEGER,        -- Nullable (NEW)
    -- Same check constraint
);
```

### German Naming Convention
ALL database objects use German names:
- Table names: `patienten`, `therapeuten`, `platzsuche`
- Column names: `vorname`, `nachname`, `geburtsdatum`
- Enum values: `auf_der_Suche`, `vollstaendige_Annahme`

## Current Schema Overview

### Enum Types (German values)
```sql
patientenstatus: offen, auf_der_Suche, in_Therapie...
therapeutstatus: aktiv, gesperrt, inaktiv
emailstatus: Entwurf, In_Warteschlange, Gesendet...
suchstatus: aktiv, erfolgreich, pausiert, abgebrochen
antworttyp: vollstaendige_Annahme, teilweise_Annahme...
```

### Service Schemas
1. **patient_service**: `patienten` table
2. **therapist_service**: `therapeuten` table  
3. **matching_service**: Bundle system tables
4. **communication_service**: Emails/calls with patient support
5. **geocoding_service**: Cache tables (English - technical)

## Key Features

### Bundle System Tables
- `platzsuche`: Patient search tracking
- `therapeutenanfrage`: Bundles sent to therapists
- `therapeut_anfrage_patient`: Bundle composition

### Foreign Key Relationships
- Cross-schema references maintained
- Cascade deletes where appropriate
- Set null for communication references

### Indexes
Optimized for common queries:
- Status filtering
- Date-based queries
- Foreign key lookups

## Migration History
Single comprehensive migration (`001_initial_setup.py`):
- Creates all schemas
- Defines all enums with German values
- Creates all tables with constraints
- Adds all foreign keys
- Creates all indexes

## Service Status
| Service | Database | Models | APIs | Status |
|---------|----------|--------|------|--------|
| Patient | German ✅ | German ✅ | German ✅ | Operational |
| Therapist | German ✅ | German ✅ | German ✅ | Operational |
| Matching | German ✅ | German ✅ | German ✅ | Operational |
| Communication | German ✅ | German ✅ | German ✅ | Operational |
| Geocoding | English ✅ | English ✅ | English ✅ | Operational |

## Quick Reference

### Patient Communication
```sql
-- Find all emails for a patient
SELECT * FROM communication_service.emails 
WHERE patient_id = 123;

-- Find all scheduled calls for patients
SELECT * FROM communication_service.telefonanrufe
WHERE patient_id IS NOT NULL 
  AND status = 'geplant';
```

### Bundle Queries
```sql
-- Active bundles awaiting response
SELECT * FROM matching_service.therapeutenanfrage
WHERE gesendet_datum IS NOT NULL 
  AND antwort_datum IS NULL;
```

## Notes
- PlacementRequest table: REMOVED (replaced by bundle system)
- Batch tables: REMOVED (logic in matching service)
- All timestamps: UTC
- All services: Using PgBouncer for connections