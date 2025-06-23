# Database Schema - FINAL State

> **Note**: Complete schema in `migrations/alembic/versions/001_initial_setup.py`

## Summary
FINAL production schema with full German naming convention and comprehensive patient communication support. All migrations applied, all services operational.

## Schema Overview ✅ COMPLETE

### German Naming Convention
ALL database objects use German names for consistency:
- **Table names**: `patienten`, `therapeuten`, `platzsuche`, `telefonanrufe`
- **Column names**: `vorname`, `nachname`, `geburtsdatum`, `naechster_kontakt_moeglich`
- **Enum values**: `auf_der_Suche`, `vollstaendige_Annahme`, `geplant`

### Service Schemas
1. **patient_service**: Patient data and preferences
2. **therapist_service**: Therapist profiles and availability  
3. **matching_service**: Anfrage system tables
4. **communication_service**: Emails and calls with dual recipient support
5. **geocoding_service**: Cache tables (English - technical only)

## Core Schema Features

### Dual Recipient Communication
Communication Service tables support BOTH therapists AND patients:

```sql
-- Emails table with dual recipient support
CREATE TABLE communication_service.emails (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER,      -- References therapist_service.therapeuten.id
    patient_id INTEGER,        -- References patient_service.patienten.id
    betreff VARCHAR(255) NOT NULL,
    empfaenger_email VARCHAR(255) NOT NULL,
    status emailstatus DEFAULT 'Entwurf',
    -- Check constraint: exactly one recipient must be set
    CONSTRAINT check_single_recipient CHECK (
        (therapist_id IS NOT NULL AND patient_id IS NULL) OR 
        (therapist_id IS NULL AND patient_id IS NOT NULL)
    )
);

-- Phone calls with same dual recipient pattern
CREATE TABLE communication_service.telefonanrufe (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER,      -- Nullable  
    patient_id INTEGER,        -- Nullable
    geplantes_datum DATE NOT NULL,
    geplante_zeit TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'geplant',
    -- Same check constraint for single recipient
    CONSTRAINT check_single_recipient CHECK (
        (therapist_id IS NOT NULL AND patient_id IS NULL) OR 
        (therapist_id IS NULL AND patient_id IS NOT NULL)
    )
);
```

### Enum Types (German Values)
```sql
-- Patient status progression
CREATE TYPE patientenstatus AS ENUM (
    'offen', 'auf_der_Suche', 'in_Therapie', 
    'Therapie_abgeschlossen', 'Suche_abgebrochen', 'Therapie_abgebrochen'
);

-- Therapist operational status
CREATE TYPE therapeutstatus AS ENUM ('aktiv', 'gesperrt', 'inaktiv');

-- Email delivery status
CREATE TYPE emailstatus AS ENUM (
    'Entwurf', 'In_Warteschlange', 'Wird_gesendet', 'Gesendet', 'Fehlgeschlagen'
);

-- Patient search status
CREATE TYPE suchstatus AS ENUM ('aktiv', 'erfolgreich', 'pausiert', 'abgebrochen');

-- Anfrage response types
CREATE TYPE antworttyp AS ENUM (
    'vollstaendige_Annahme', 'teilweise_Annahme', 
    'vollstaendige_Ablehnung', 'keine_Antwort'
);

-- Individual patient outcomes
CREATE TYPE patientenergebnis AS ENUM (
    'angenommen', 'abgelehnt_Kapazitaet', 'abgelehnt_nicht_geeignet',
    'abgelehnt_sonstiges', 'nicht_erschienen', 'in_Sitzungen'
);

-- Phone call status
CREATE TYPE telefonanrufstatus AS ENUM (
    'geplant', 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen'
);

-- Gender preferences
CREATE TYPE therapeutgeschlechtspraeferenz AS ENUM ('Männlich', 'Weiblich', 'Egal');

-- Therapy procedures
CREATE TYPE therapieverfahren AS ENUM (
    'egal', 'Verhaltenstherapie', 'tiefenpsychologisch_fundierte_Psychotherapie'
);
```

## Key Schema Changes from Original Design

### Patient Model Enhancements
- **Added fields**: `symptome`, `erfahrung_mit_psychotherapie` 
- **Updated preferences**: `bevorzugtes_therapieverfahren` as PostgreSQL ARRAY
- **Removed fields**: `bevorzugtes_therapeutenalter_min/max` (age preferences moved to therapist model)

### Therapist Model Updates
- **New field**: `ueber_curavani_informiert` (boolean flag for tracking)
- **Anfrage preferences**: `bevorzugte_diagnosen`, `alter_min/max`, `geschlechtspraeferenz`
- **Contact tracking**: Separate fields for email/phone/personal contact dates

### Anfrage System Tables
Complete replacement of original bundle system:

```sql
-- Patient search tracking
CREATE TABLE matching_service.platzsuche (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    status suchstatus DEFAULT 'aktiv',
    ausgeschlossene_therapeuten JSONB DEFAULT '[]',
    gesamt_angeforderte_kontakte INTEGER DEFAULT 0,
    erfolgreiche_vermittlung_datum DATE,
    notizen TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Therapist inquiries  
CREATE TABLE matching_service.therapeutenanfrage (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    erstellt_datum TIMESTAMP DEFAULT NOW(),
    gesendet_datum TIMESTAMP,
    antwort_datum TIMESTAMP,
    antworttyp antworttyp,
    anfragegroesse INTEGER NOT NULL,
    angenommen_anzahl INTEGER DEFAULT 0,
    abgelehnt_anzahl INTEGER DEFAULT 0,
    keine_antwort_anzahl INTEGER DEFAULT 0,
    email_id INTEGER,
    phone_call_id INTEGER,
    notizen TEXT
);

-- Anfrage composition
CREATE TABLE matching_service.therapeut_anfrage_patient (
    id SERIAL PRIMARY KEY,
    therapeutenanfrage_id INTEGER NOT NULL REFERENCES matching_service.therapeutenanfrage(id),
    platzsuche_id INTEGER NOT NULL REFERENCES matching_service.platzsuche(id),
    patient_id INTEGER NOT NULL,
    position_in_anfrage INTEGER NOT NULL,
    status anfrage_patient_status DEFAULT 'anstehend',
    antwortergebnis patientenergebnis,
    antwortnotizen TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Indexing Strategy

### Performance Indexes
```sql
-- Communication queries
CREATE INDEX idx_emails_therapist_id ON communication_service.emails(therapist_id);
CREATE INDEX idx_emails_patient_id ON communication_service.emails(patient_id);
CREATE INDEX idx_emails_status ON communication_service.emails(status);
CREATE INDEX idx_telefonanrufe_therapist_id ON communication_service.telefonanrufe(therapist_id);
CREATE INDEX idx_telefonanrufe_patient_id ON communication_service.telefonanrufe(patient_id);

-- Matching system queries
CREATE INDEX idx_platzsuche_patient_id ON matching_service.platzsuche(patient_id);
CREATE INDEX idx_platzsuche_status ON matching_service.platzsuche(status);
CREATE INDEX idx_therapeutenanfrage_therapist_id ON matching_service.therapeutenanfrage(therapist_id);
CREATE INDEX idx_therapeutenanfrage_gesendet_datum ON matching_service.therapeutenanfrage(gesendet_datum);

-- Service-specific indexes
CREATE INDEX idx_patienten_status ON patient_service.patienten(status);
CREATE INDEX idx_therapeuten_status ON therapist_service.therapeuten(status);
CREATE INDEX idx_therapeuten_potenziell_verfuegbar ON therapist_service.therapeuten(potenziell_verfuegbar);
```

## Data Relationships

### Cross-Service References
- **Simple integers**: All foreign keys to other services use simple INTEGER types
- **No database FKs**: Cross-service references handled at application level
- **Service boundaries**: Each service owns its schema completely

### Intra-Service References
- **Proper FKs**: Within-service relationships use database foreign keys
- **Cascade rules**: Appropriate CASCADE/SET NULL rules for data integrity
- **Referential integrity**: Database-enforced consistency within schemas

## Migration History

### Single Comprehensive Migration
File: `migrations/alembic/versions/001_initial_setup.py`
- Creates all schemas and tables
- Defines all German enums with proper values  
- Establishes all foreign key relationships
- Creates all performance indexes
- Sets up proper constraints and defaults

### Version Control Strategy
- **Single migration**: Simplified deployment with one comprehensive migration
- **Schema versioning**: Alembic tracks schema version for future changes
- **Rollback capability**: Complete schema can be rolled back if needed

## Service Status Summary

| Service | Database | Models | APIs | Integration | Status |
|---------|----------|--------|------|-------------|--------|
| Patient | German ✅ | German ✅ | German ✅ | Complete ✅ | Operational |
| Therapist | German ✅ | German ✅ | German ✅ | Complete ✅ | Operational |
| Matching | German ✅ | German ✅ | German ✅ | Complete ✅ | Operational |
| Communication | German ✅ | German ✅ | German ✅ | Complete ✅ | Operational |
| Geocoding | English ✅ | English ✅ | English ✅ | Complete ✅ | Operational |

## Quick Reference Queries

### Patient Communication History
```sql
-- Find all communications for a patient
SELECT 'email' as type, id, betreff as subject, status, gesendet_am as date
FROM communication_service.emails 
WHERE patient_id = $1
UNION ALL
SELECT 'call' as type, id, notizen as subject, status, 
       CONCAT(geplantes_datum, ' ', geplante_zeit) as date
FROM communication_service.telefonanrufe
WHERE patient_id = $1
ORDER BY date DESC;
```

### Active Anfragen Status
```sql
-- Active anfragen awaiting response
SELECT ta.id, ta.therapist_id, ta.anfragegroesse,
       ta.gesendet_datum, 
       (NOW() - ta.gesendet_datum)::INTEGER as tage_seit_versand
FROM matching_service.therapeutenanfrage ta
WHERE ta.gesendet_datum IS NOT NULL 
  AND ta.antwort_datum IS NULL
ORDER BY ta.gesendet_datum;
```

### Therapist Availability
```sql
-- Available therapists not in cooling period
SELECT id, vorname, nachname, potenziell_verfuegbar, 
       ueber_curavani_informiert, naechster_kontakt_moeglich
FROM therapist_service.therapeuten
WHERE status = 'aktiv'
  AND (naechster_kontakt_moeglich IS NULL 
       OR naechster_kontakt_moeglich <= CURRENT_DATE);
```

## Notes
- **All timestamps**: UTC timezone
- **All services**: Using PgBouncer for connection pooling
- **Cross-service calls**: HTTP APIs for data access between services
- **Event streaming**: Kafka for asynchronous communication
- **Schema stability**: No planned major changes to current structure