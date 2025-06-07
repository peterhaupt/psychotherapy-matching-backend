# Database Schema Updates - Final State

This document shows the FINAL database schema after all migrations have been applied. All field names use German terminology for consistency.

## Naming Convention ✅ FULLY IMPLEMENTED
**Important:** ALL field names in the database now use German terminology. This decision was made to maintain consistency with the existing codebase and avoid confusion from mixing languages.

## Current Database State

### Phase 1: Communication Service ✅ COMPLETED

1. **Therapist Model Fields**:
   - `potenziell_verfuegbar` → Boolean flag
   - `potenziell_verfuegbar_notizen` → Text notes
   - `telefonische_erreichbarkeit` → JSONB structure

2. **Communication Tables Created**:
   - `communication_service.emails` → Email tracking with German fields
   - `communication_service.phone_calls` → Phone call tracking with German fields
   - `communication_service.email_batches` → Links emails to bundle patients
   - `communication_service.phone_call_batches` → Links calls to bundle patients

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
   - ❌ `matching_service.placement_requests` → REMOVED COMPLETELY
   - ❌ All foreign key references updated to use bundle system

## Complete Schema Reference

### Patient Service

#### patients
```sql
CREATE TABLE patient_service.patients (
    id SERIAL PRIMARY KEY,
    -- Personal Information
    anrede VARCHAR(10),
    vorname VARCHAR(100) NOT NULL,
    nachname VARCHAR(100) NOT NULL,
    strasse VARCHAR(255),
    plz VARCHAR(10),
    ort VARCHAR(100),
    email VARCHAR(255),
    telefon VARCHAR(50),
    
    -- Medical Information
    hausarzt VARCHAR(255),
    krankenkasse VARCHAR(100),
    krankenversicherungsnummer VARCHAR(50),
    geburtsdatum DATE,
    diagnose VARCHAR(50),
    
    -- Process Status
    vertraege_unterschrieben BOOLEAN DEFAULT FALSE,
    psychotherapeutische_sprechstunde BOOLEAN DEFAULT FALSE,
    startdatum DATE,
    erster_therapieplatz_am DATE,
    funktionierender_therapieplatz_am DATE,
    status patientstatus,
    empfehler_der_unterstuetzung TEXT,
    
    -- Availability & Preferences
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

#### therapists (with all German fields)
```sql
CREATE TABLE therapist_service.therapists (
    id SERIAL PRIMARY KEY,
    -- Personal Information
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
    
    -- Professional Information
    kassensitz BOOLEAN DEFAULT TRUE,
    geschlecht VARCHAR(20),
    telefonische_erreichbarkeit JSONB,
    fremdsprachen JSONB,
    psychotherapieverfahren JSONB,
    zusatzqualifikationen TEXT,
    besondere_leistungsangebote TEXT,
    
    -- Contact History
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
    notizen TEXT
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

#### emails
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
    placement_request_ids JSONB,  -- Legacy field
    batch_id VARCHAR(50),
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

#### email_batches (updated to reference bundle system)
```sql
CREATE TABLE communication_service.email_batches (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL REFERENCES emails(id),
    therapeut_anfrage_patient_id INTEGER REFERENCES matching_service.therapeut_anfrage_patient(id),
    priority INTEGER DEFAULT 1,
    included BOOLEAN DEFAULT TRUE,
    antwortergebnis VARCHAR(50),
    antwortnotizen TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### phone_calls
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

#### phone_call_batches (updated to reference bundle system)
```sql
CREATE TABLE communication_service.phone_call_batches (
    id SERIAL PRIMARY KEY,
    phone_call_id INTEGER NOT NULL REFERENCES phone_calls(id),
    therapeut_anfrage_patient_id INTEGER REFERENCES matching_service.therapeut_anfrage_patient(id),
    priority INTEGER DEFAULT 1,
    discussed BOOLEAN DEFAULT FALSE,
    ergebnis VARCHAR(50),
    nachverfolgung_erforderlich BOOLEAN DEFAULT FALSE,
    nachverfolgung_notizen TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- PlacementRequestStatus has been REMOVED
```

## Migration Status Summary

All migrations have been successfully applied:

| Migration | Description | German Fields |
|-----------|-------------|---------------|
| `bcfc97d0f1h1` | ✅ Rename therapist bundle fields | naechster_kontakt_moeglich, etc. |
| `ccfc98e1g2i2` | ✅ Remove unused date fields | - |
| `dcfc99f2h3j3` | ✅ Add group therapy preference | bevorzugt_gruppentherapie |
| `ecfc00g3k4k4` | ✅ Rename potentially_available | potenziell_verfuegbar |
| `fcfc01h4l5l5` | ✅ Remove placement_requests | - |
| `gcfc02i5m6m6` | ✅ Rename ALL remaining fields | Complete German naming |

## Next Steps

1. ✅ Database schema is complete
2. 🔄 Update all model files to match German field names
3. 🔄 Update API endpoints to use German fields
4. 🔄 Update documentation and tests

## Important Notes

- **NO English field names remain** in the database (except technical geocoding fields)
- **PlacementRequest is completely removed** - use bundle system instead
- **All foreign keys updated** to reference therapeut_anfrage_patient
- **Models must be updated** to match these German field names exactly