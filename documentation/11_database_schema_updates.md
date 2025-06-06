# Database Schema Updates for Communication Service and Bundle System

This document describes the database schema changes required to implement the communication service's email batching, phone call scheduling functionality, and the bundle-based matching system.

## Naming Convention
**Important:** All field names in the database use German terminology to maintain consistency with the existing codebase. This decision was made to avoid confusion from mixing English and German field names.

## Overview of Changes

### Phase 1: Communication Service ✅ COMPLETED

1. **Therapist Model Updates**:
   - `potentially_available` → Boolean flag
   - `potentially_available_notes` → Text notes
   - `telefonische_erreichbarkeit` → JSONB structure (already existed)

2. **New Tables Created**:
   - `communication_service.phone_calls` → Phone call tracking
   - `communication_service.phone_call_batches` → Bundle calls with placement requests
   - `communication_service.email_batches` → Bundle emails with placement requests

3. **Email Table Updates**:
   - Added response tracking fields
   - Added batch management fields

### Phase 2: Bundle System 🔄 IN PROGRESS

1. **Therapist Table Extensions** (Migration: `acfc96c9f0g0`):
   - `next_contactable_date` → `naechster_kontakt_moeglich` (Date)
   - `preferred_diagnoses` → `bevorzugte_diagnosen` (JSONB)
   - `age_min` → `alter_min` (Integer)
   - `age_max` → `alter_max` (Integer)
   - `gender_preference` → `geschlechtspraeferenz` (String)
   - `working_hours` → `arbeitszeiten` (JSONB)

2. **New Bundle Tables**:
   - `matching_service.platzsuche` → Patient search tracking
   - `matching_service.therapeutenanfrage` → Therapist inquiry (bundle)
   - `matching_service.therapeut_anfrage_patient` → Bundle composition

## Detailed Schema Changes

### 1. Updated Therapist Table

```sql
-- Already implemented fields (German names)
ALTER TABLE therapist_service.therapists
ADD COLUMN potentially_available BOOLEAN DEFAULT FALSE,
ADD COLUMN potentially_available_notes TEXT;

-- New bundle-related fields (being renamed to German)
ALTER TABLE therapist_service.therapists
ADD COLUMN naechster_kontakt_moeglich DATE,
ADD COLUMN bevorzugte_diagnosen JSONB,
ADD COLUMN alter_min INTEGER,
ADD COLUMN alter_max INTEGER,
ADD COLUMN geschlechtspraeferenz VARCHAR(50),
ADD COLUMN arbeitszeiten JSONB;
```

The `telefonische_erreichbarkeit` field structure:
```json
{
  "montag": [
    {"start": "09:00", "end": "12:00"},
    {"start": "14:00", "end": "16:30"}
  ],
  "mittwoch": [
    {"start": "10:00", "end": "14:00"}
  ],
  "freitag": [
    {"start": "08:30", "end": "11:30"}
  ]
}
```

### 2. Patient Table (No Changes Needed)

The existing Patient model already has sufficient fields:
- `raeumliche_verfuegbarkeit` (JSONB) → Can store `{"max_km": 30}`
- `verkehrsmittel` (String) → Already handles "Auto" or "ÖPNV"
- `zeitliche_verfuegbarkeit` (JSONB) → Detailed availability

No additional migration needed for patients.

### 3. Bundle System Tables

#### Platzsuche (Patient Search)
```sql
CREATE TABLE matching_service.platzsuche (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    excluded_therapists JSONB DEFAULT '[]',
    total_requested_contacts INTEGER DEFAULT 0,
    successful_match_date TIMESTAMP,
    notes TEXT
);
```

#### Therapeutenanfrage (Therapist Inquiry/Bundle)
```sql
CREATE TABLE matching_service.therapeutenanfrage (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_date TIMESTAMP,
    response_date TIMESTAMP,
    response_type VARCHAR(50),
    bundle_size INTEGER,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    no_response_count INTEGER DEFAULT 0,
    notes TEXT
);
```

#### Therapeut Anfrage Patient (Bundle Composition)
```sql
CREATE TABLE matching_service.therapeut_anfrage_patient (
    id SERIAL PRIMARY KEY,
    therapeutenanfrage_id INTEGER NOT NULL,
    platzsuche_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    position_in_bundle INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    response_outcome VARCHAR(50),
    response_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Migration Status

| Migration | Status | Description |
|-----------|--------|-------------|
| `6fbc92a7b7e9` | ✅ Applied | Add potentially available fields |
| `7bfc93a7c8e9` | ✅ Applied | Create phone call tables |
| `8bfc94a7d8f9` | ✅ Applied | Add email batch table |
| `9cfc95b8e9f9` | ✅ Applied | Create geocoding tables |
| `be3c0220ee8c` | ✅ Applied | Update EmailStatus enum to English |
| `acfc96c9f0g0` | ✅ Applied | Add bundle system tables |
| `bcfc97d0f1h1` | 🔄 Pending | Rename therapist fields to German |

## Implementation Notes

### German Naming Conventions

All new fields follow German naming patterns:
- Use underscores for compound words: `naechster_kontakt_moeglich`
- Match existing patterns: `telefonische_erreichbarkeit`
- Keep technical terms simple: `status`, `id`

### Bundle System Logic

The schema supports:
1. **Cooling Period**: Tracked via `naechster_kontakt_moeglich` on therapist
2. **Parallel Search**: Patient can be in multiple `therapeutenanfrage` bundles
3. **Conflict Resolution**: `status` field in `therapeut_anfrage_patient` tracks outcomes
4. **Progressive Filtering**: Preferences stored in therapist fields

### Helper Methods in Models

The Therapist model includes helper methods:
- `get_available_slots()`: Parse `telefonische_erreichbarkeit`
- `is_available_at()`: Check specific time availability
- `get_next_available_slot()`: Find next open slot

## Next Steps

1. ✅ Apply migration to rename fields to German
2. 📋 Update Therapist model with new German field names
3. 📋 Create SQLAlchemy models for bundle tables
4. 📋 Implement bundle algorithm using these schemas