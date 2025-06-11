# Database German Migration Plan

## Overview
This document outlines all database changes needed to achieve full German consistency in the Psychotherapy Matching Platform. The changes affect table names, column names, enum type names, and enum values.

## Migration Scope

### Summary Statistics
- **3** table names to change
- **8** column names to change  
- **8** enum type names to change
- **24** enum values to change to German
- **3** enum types already have correct German values

---

## 1. Table Name Changes

### Patient Service
```sql
patients → patienten
```

### Therapist Service  
```sql
therapists → therapeuten
```

### Communication Service
```sql
phone_calls → telefonanrufe
```

---

## 2. Column Name Changes

### Communication Service - emails table
```sql
body_html → inhalt_html
body_text → inhalt_text
queued_at → in_warteschlange_am
sent_at → gesendet_am
```

### Matching Service - therapeutenanfrage table
```sql
created_date → erstellt_datum
sent_date → gesendet_datum
response_date → antwort_datum
```

---

## 3. Enum Type Name Changes

```sql
patientstatus → patientenstatus
therapiststatus → therapeutstatus
therapistgenderpreference → therapeutgeschlechtspraeferenz
searchstatus → suchstatus
phonecallstatus → telefonanrufstatus
responsetype → antworttyp
patientoutcome → patientenergebnis
emailstatus → emailstatus (stays the same)
```

---

## 4. Enum Value Changes

### patientenstatus (currently patientstatus)
| Current Value | New German Value |
|--------------|------------------|
| `OPEN` | `offen` |
| `SEARCHING` | `auf_der_Suche` |
| `IN_THERAPY` | `in_Therapie` |
| `THERAPY_COMPLETED` | `Therapie_abgeschlossen` |
| `SEARCH_ABORTED` | `Suche_abgebrochen` |
| `THERAPY_ABORTED` | `Therapie_abgebrochen` |

### therapeutstatus (currently therapiststatus)
| Current Value | New German Value |
|--------------|------------------|
| `ACTIVE` | `aktiv` |
| `BLOCKED` | `gesperrt` |
| `INACTIVE` | `inaktiv` |

### emailstatus
| Current Value | New German Value |
|--------------|------------------|
| `DRAFT` | `Entwurf` |
| `QUEUED` | `In_Warteschlange` |
| `SENDING` | `Wird_gesendet` |
| `SENT` | `Gesendet` |
| `FAILED` | `Fehlgeschlagen` |

### antworttyp (currently responsetype)
| Current Value | New German Value |
|--------------|------------------|
| `FULL_ACCEPTANCE` | `vollstaendige_Annahme` |
| `PARTIAL_ACCEPTANCE` | `teilweise_Annahme` |
| `FULL_REJECTION` | `vollstaendige_Ablehnung` |
| `NO_RESPONSE` | `keine_Antwort` |

### patientenergebnis (currently patientoutcome)
| Current Value | New German Value |
|--------------|------------------|
| `ACCEPTED` | `angenommen` |
| `REJECTED_CAPACITY` | `abgelehnt_Kapazitaet` |
| `REJECTED_NOT_SUITABLE` | `abgelehnt_nicht_geeignet` |
| `REJECTED_OTHER` | `abgelehnt_sonstiges` |
| `NO_SHOW` | `nicht_erschienen` |
| `IN_SESSIONS` | `in_Sitzungen` |

---

## 5. Already Correct - No Changes Needed

### ✓ suchstatus (currently searchstatus)
Already has German values:
- `aktiv`
- `erfolgreich`
- `pausiert`
- `abgebrochen`

### ✓ telefonanrufstatus (currently phonecallstatus)
Already has German values:
- `geplant`
- `abgeschlossen`
- `fehlgeschlagen`
- `abgebrochen`

### ✓ therapeutgeschlechtspraeferenz (currently therapistgenderpreference)
Already has German values:
- `Männlich`
- `Weiblich`
- `Egal`

---

## 6. Fields That Stay in English

### Technical Convention Fields (All Tables)
- `id` - Primary key convention
- `created_at` - Timestamp convention
- `updated_at` - Timestamp convention
- All foreign keys ending in `_id` (e.g., `patient_id`, `therapist_id`)
- `status` - Common technical term (in some contexts)

### Geocoding Service
All geocoding fields remain in English as they are technical/geographic terms:
- `origin_latitude`, `origin_longitude`
- `destination_latitude`, `destination_longitude`
- `travel_mode`, `distance_km`, `travel_time_minutes`
- `query`, `query_type`, `display_name`
- etc.

---

## Implementation Order

### Phase 1: Enum Changes
1. Create new enum types with German names
2. Migrate enum values to German
3. Update all references in code
4. Drop old enum types

### Phase 2: Column Name Changes
1. Rename columns using ALTER TABLE statements
2. Update all model definitions
3. Update all API references

### Phase 3: Table Name Changes
1. Rename tables
2. Update all foreign key constraints
3. Update all model table references
4. Update all queries

---

## Notes

1. **Consistency Rule**: All multi-word values use underscores (e.g., `auf_der_Suche` not `auf der Suche`)
2. **Capitalization**: Follow German noun capitalization rules where appropriate
3. **Special Characters**: Avoid umlauts in database names (use `ae`, `oe`, `ue`)
4. **Testing**: Each phase should be thoroughly tested before proceeding to the next

---

## Migration Checklist

- [ ] Phase 1: Enum Changes
  - [ ] Create migration for enum type renames
  - [ ] Create migration for enum value updates
  - [ ] Update all Python enum definitions
  - [ ] Update SQLAlchemy models
  - [ ] Test all enum operations
  
- [ ] Phase 2: Column Name Changes
  - [ ] Create migration for column renames
  - [ ] Update all model definitions
  - [ ] Update all API endpoints
  - [ ] Update all queries
  - [ ] Test all CRUD operations
  
- [ ] Phase 3: Table Name Changes
  - [ ] Create migration for table renames
  - [ ] Update all model table references
  - [ ] Update all foreign key constraints
  - [ ] Update all schema references
  - [ ] Full integration test

---

*Document created: December 2024*
*Last updated: December 2024*