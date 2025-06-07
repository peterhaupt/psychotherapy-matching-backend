# Database Schema Updates - Final State

This document shows the FINAL database schema after all migrations have been applied. All field names use German terminology for consistency.

## Naming Convention ✅ FULLY IMPLEMENTED IN DATABASE
**Important:** ALL field names in the database now use German terminology. This decision was made to maintain consistency with the existing codebase and avoid confusion from mixing languages.

**Current Status:**
- ✅ Database: 100% German field names
- ✅ Patient Service: Models and APIs use German
- ❌ Therapist Service: Models still use English (causing errors)
- ✅ Matching Service: PlacementRequest removed, stub models use German
- ✅ Communication Service: Models and APIs updated to German

## Current Database State

### Phase 1: Communication Service ✅ COMPLETED

1. **Therapist Model Fields**:
   - `potenziell_verfuegbar` → Boolean flag
   - `potenziell_verfuegbar_notizen` → Text notes
   - `telefonische_erreichbarkeit` → JSONB structure

2. **Communication Tables Created**:
   - `communication_service.emails` → Email tracking with German fields
   - `communication_service.phone_calls` → Phone call tracking with German fields
   - ~~`communication_service.email_batches`~~ → **REMOVED** (moved to matching service)
   - ~~`communication_service.phone_call_batches`~~ → **REMOVED** (moved to matching service)

### Phase 2: Bundle System ✅ COMPLETED

1. **Therapist Table Extensions**:
   - `naechster_kontakt_moeglich` → Date (cooling period)
   - `bevorzugte_diagnosen` → JSONB (preferred ICD-10 codes)
   - `alter_min` → Integer (minimum patient age)
   - `alter_max` → Integer (maximum patient age)
   - `geschlechtspraeferenz` → String (patient gender preference)
   - `arbeitszeiten` → JSONB (working hours)
   - `bevorzugt_gruppentherapie` → Boolean (group therapy preference)

2. **Bundle Tables Created**:
   - `matching_service.platzsuche` → Patient search tracking
   - `matching_service.therapeutenanfrage` → Therapist inquiry (bundle)
   - `matching_service.therapeut_anfrage_patient` → Bundle composition

3. **PlacementRequest Removal**:
   - ✅ `matching_service.placement_requests` → **REMOVED FROM DATABASE**
   - ✅ All foreign key references updated to use bundle system
   - ✅ **PlacementRequest code completely removed from codebase**

### Phase 3: Communication Service Simplification ✅ COMPLETED

1. **Removed Batch Tables**:
   - ❌ `communication_service.email_batches` → **REMOVED**
   - ❌ `communication_service.phone_call_batches` → **REMOVED**

2. **Added Bundle References**:
   - `matching_service.therapeutenanfrage.email_id` → References communication emails
   - `matching_service.therapeutenanfrage.phone_call_id` → References communication calls

## Complete Schema Reference (Current State in Database)

### Patient Service

#### patients
```sql
CREATE TABLE patient_service.patients (
    id SERIAL PRIMARY KEY,
    -- Personal Information (German names)
    anrede VARCHAR(10),
    vorname VARCHAR(100) NOT NULL,
    nachname VARCHAR(100) NOT NULL,
    strasse VARCHAR(255),
    plz VARCHAR(10),
    ort VARCHAR(100),
    email VARCHAR(255),
    telefon VARCHAR(50),
    
    -- Medical Information (German names)
    hausarzt VARCHAR(255),
    krankenkasse VARCHAR(100),
    krankenversicherungsnummer VARCHAR(50),
    geburtsdatum DATE,
    diagnose VARCHAR(50),
    
    -- Process Status (German names)
    vertraege_unterschrieben BOOLEAN DEFAULT FALSE,
    psychotherapeutische_sprechstunde BOOLEAN DEFAULT FALSE,
    startdatum DATE,
    erster_therapieplatz_am DATE,
    funktionierender_therapieplatz_am DATE,
    status patientstatus,
    empfehler_der_unterstuetzung TEXT,
    
    -- Availability & Preferences (German names)
    zeitliche_verfuegbarkeit JSONB,
    raeumliche_verfuegbarkeit JSONB,
    verkehrsmittel VARCHAR(50),
    offen_fuer_gruppentherapie BOOLEAN DEFAULT FALSE,
    offen_fuer_diga BOOLEAN DEFAULT FALSE,
    ausgeschlossene_therapeuten JSONB,
    bevorzugtes_therapeutengeschlecht therapistgenderpreference,
    
    -- Additional fields...
    created_at DATE,
    updated_at DATE
);
```

### Therapist Service

#### therapists (ALL German fields)
```sql
CREATE TABLE therapist_service.therapists (
    id SERIAL PRIMARY KEY,
    -- Personal Information (German names)
    anrede VARCHAR(10),
    titel VARCHAR(20),
    vorname VARCHAR(100) NOT NULL,
    nachname VARCHAR(100) NOT NULL,
    strasse VARCHAR(255),
    plz VARCHAR(10),
    ort VARCHAR(100),
    telefon VARCHAR(50),
    fax VARCHAR(50),
    email VARCHAR(255),
    webseite VARCHAR(255),
    
    -- Professional Information (German names)
    kassensitz BOOLEAN DEFAULT TRUE,
    geschlecht VARCHAR(20),
    telefonische_erreichbarkeit JSONB,
    fremdsprachen JSONB,
    psychotherapieverfahren JSONB,
    zusatzqualifikationen TEXT,
    besondere_leistungsangebote TEXT,
    
    -- Contact History (German names)
    letzter_kontakt_email DATE,
    letzter_kontakt_telefon DATE,
    letztes_persoenliches_gespraech DATE,
    
    -- Availability (German names)
    potenziell_verfuegbar BOOLEAN DEFAULT FALSE,
    potenziell_verfuegbar_notizen TEXT,
    
    -- Bundle System Fields (German names)
    naechster_kontakt_moeglich DATE,
    bevorzugte_diagnosen JSONB,
    alter_min INTEGER,
    alter_max INTEGER,
    geschlechtspraeferenz VARCHAR(50),
    arbeitszeiten JSONB,
    bevorzugt_gruppentherapie BOOLEAN DEFAULT FALSE,
    
    -- Status
    status therapiststatus DEFAULT 'aktiv',
    sperrgrund TEXT,
    sperrdatum DATE,
    
    created_at DATE,
    updated_at DATE
);
```

### Matching Service (Bundle System)

#### platzsuche (Patient Search)
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

#### therapeutenanfrage (Therapist Inquiry/Bundle)
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
    -- References to communication service
    email_id INTEGER REFERENCES communication_service.emails(id),
    phone_call_id INTEGER REFERENCES communication_service.phone_calls(id)
);
```

#### therapeut_anfrage_patient (Bundle Composition)
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

### Communication Service (with German fields)

#### emails (German field names)
```sql
CREATE TABLE communication_service.emails (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    betreff VARCHAR(255) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT NOT NULL,
    empfaenger_email VARCHAR(255) NOT NULL,
    empfaenger_name VARCHAR(255) NOT NULL,
    absender_email VARCHAR(255) NOT NULL,
    absender_name VARCHAR(255) NOT NULL,
    antwort_erhalten BOOLEAN DEFAULT FALSE,
    antwortdatum TIMESTAMP,
    antwortinhalt TEXT,
    nachverfolgung_erforderlich BOOLEAN DEFAULT FALSE,
    nachverfolgung_notizen TEXT,
    status emailstatus DEFAULT 'DRAFT',
    queued_at TIMESTAMP,
    sent_at TIMESTAMP,
    fehlermeldung TEXT,
    wiederholungsanzahl INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### phone_calls (German field names)
```sql
CREATE TABLE communication_service.phone_calls (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    geplantes_datum DATE NOT NULL,
    geplante_zeit TIME NOT NULL,
    dauer_minuten INTEGER DEFAULT 5,
    tatsaechliches_datum DATE,
    tatsaechliche_zeit TIME,
    status VARCHAR(50) DEFAULT 'scheduled',
    ergebnis TEXT,
    notizen TEXT,
    wiederholen_nach DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Geocoding Service (technical fields remain in English)

#### geocache
```sql
CREATE TABLE geocoding_service.geocache (
    id SERIAL PRIMARY KEY,
    query VARCHAR(255) NOT NULL,
    query_type VARCHAR(50) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    display_name VARCHAR(255),
    result_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    hit_count INTEGER DEFAULT 1
);
```

#### distance_cache
```sql
CREATE TABLE geocoding_service.distance_cache (
    id SERIAL PRIMARY KEY,
    origin_latitude FLOAT NOT NULL,
    origin_longitude FLOAT NOT NULL,
    destination_latitude FLOAT NOT NULL,
    destination_longitude FLOAT NOT NULL,
    travel_mode VARCHAR(50) NOT NULL,
    distance_km FLOAT NOT NULL,
    travel_time_minutes FLOAT,
    route_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    hit_count INTEGER DEFAULT 1
);
```

## Enum Types

```sql
-- Patient status
CREATE TYPE patientstatus AS ENUM (
    'OPEN', 'SEARCHING', 'IN_THERAPY', 
    'THERAPY_COMPLETED', 'SEARCH_ABORTED', 'THERAPY_ABORTED'
);

-- Therapist gender preference
CREATE TYPE therapistgenderpreference AS ENUM (
    'MALE', 'FEMALE', 'ANY'
);

-- Therapist status
CREATE TYPE therapiststatus AS ENUM (
    'ACTIVE', 'BLOCKED', 'INACTIVE'
);

-- Email status (in English for technical consistency)
CREATE TYPE emailstatus AS ENUM (
    'DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED'
);

-- PlacementRequestStatus has been REMOVED (table and enum deleted)
```

## Migration Status Summary

All migrations have been successfully applied:

| Migration | Status | Description |
|-----------|--------|-------------|
| `bcfc97d0f1h1` | ✅ Applied | Rename therapist bundle fields |
| `ccfc98e1g2i2` | ✅ Applied | Remove unused date fields |
| `dcfc99f2h3j3` | ✅ Applied | Add group therapy preference |
| `ecfc00g3k4k4` | ✅ Applied | Rename potentially_available |
| `fcfc01h4l5l5` | ✅ Applied | Remove placement_requests |
| `gcfc02i5m6m6` | ✅ Applied | Rename ALL remaining fields |
| `hcfc03j6n7n7` | ✅ Applied | Remove communication batch tables |

## Current Issues Due to Model/Database Mismatch

### ✅ RESOLVED: Matching Service
- **Previous Issue**: `relation "matching_service.placement_requests" does not exist`
- **Resolution**: PlacementRequest code completely removed, stub models created
- **Status**: Service returns 501 (Not Implemented) for all endpoints

### ✅ RESOLVED: Communication Service
- **Previous Issue**: Database fields didn't match model fields
- **Resolution**: All models updated to use German field names
- **Status**: Service fully operational with German field names

### Still Active Issues:

1. **Therapist Service** ⚠️
   - Database: German field names ✅
   - Model: English field names ❌
   - API: Returns English fields ❌
   - Status: GET operations work, POST/PUT may fail on new fields

## Code Update Status

### ✅ PlacementRequest Removal Complete
1. ✅ `matching_service/models/placement_request.py` - DELETED
2. ✅ `matching_service/models/__init__.py` - Import removed
3. ✅ `migrations/alembic/env.py` - Import removed
4. ✅ All API endpoints updated to return 501
5. ✅ All events updated to bundle system
6. ✅ No more PlacementRequest references in codebase

### ✅ Communication Service Update Complete
1. ✅ `communication_service/models/email.py` - Updated to German
2. ✅ `communication_service/models/phone_call.py` - Updated to German
3. ✅ `communication_service/models/email_batch.py` - DELETED
4. ✅ `communication_service/models/phone_call_batch.py` - DELETED
5. ✅ All API endpoints updated to use German fields
6. ✅ All utilities updated to use German fields

## Next Steps

1. ✅ Database schema is complete
2. ✅ PlacementRequest code removed
3. ✅ Communication Service updated to German
4. 🔄 Update therapist model to match German field names
5. 🔄 Implement full bundle system (currently stubs)

## Quick Reference: Model Updates Needed

### ✅ Communication Service (COMPLETE)
- All models updated to German
- All APIs use German field names
- Batch system removed

### ✅ Matching Service (COMPLETE - Using Stubs)
- PlacementRequest removed
- Bundle models created (basic structure)
- All imports updated
- API returns 501 for all endpoints

### Therapist Model Fields to Rename:
- `potentially_available` → `potenziell_verfuegbar`
- `potentially_available_notes` → `potenziell_verfuegbar_notizen`
- `next_contactable_date` → `naechster_kontakt_moeglich`
- `preferred_diagnoses` → `bevorzugte_diagnosen`
- `age_min` → `alter_min`
- `age_max` → `alter_max`
- `gender_preference` → `geschlechtspraeferenz`
- `working_hours` → `arbeitszeiten`
- ADD: `bevorzugt_gruppentherapie`

---
*Database State: Fully migrated to German ✅*
*Patient Service: Fully aligned with German ✅*
*Communication Service: Fully aligned with German ✅*
*Matching Service: Stable with stub implementation 🟡*
*Therapist Service: Still needs model updates ❌*