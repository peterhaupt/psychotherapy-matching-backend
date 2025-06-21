# Therapy Matching System - Implementation Plan v2.0

## Overview
Complete refactoring of the therapy matching system to implement the new manual therapist selection process with simplified matching logic and updated terminology (Bundle → Inquiry / Bündel → Anfrage).

## Phase 1: Terminology Unification ✅ COMPLETED

### 1.1 Update TERMINOLOGY.md ✅ COMPLETED

#### Core Terminology Changes:
- **Bundle** → **Inquiry** (English)
- **Bündel** → **Anfrage** (German)
- **Bundle-Based System Terms** → **Therapist Inquiry System Terms**
- **Bundle Email** → **Therapist Inquiry Email**

#### Compound Terms Updated:
| Old (Bundle-based) | New (Inquiry-based) |
|-------------------|---------------------|
| Bundle Composition | Inquiry Composition |
| Bundle Size | Inquiry Size |
| Bundle Priority | Inquiry Priority |
| Bundle Efficiency | Inquiry Efficiency |
| Optimal Bundle | Optimal Inquiry |
| Bundle Preview | Inquiry Preview |
| Bundle Response | Inquiry Response |
| Bundle IDs | Inquiry IDs |
| Bündelgröße | Anfragegröße |
| Bündelzusammensetzung | Anfragezusammensetzung |
| Bündelpriorität | Anfragepriorität |
| Bündeleffizienz | Anfrageeffizienz |
| Optimales Bündel | Optimale Anfrage |
| Bündelvorschau | Anfragevorschau |
| Bündelantwort | Anfrageantwort |
| Bündel-E-Mail | Therapeutenanfrage-E-Mail |
| Bündelerstellung | Therapeutenanfrage-Erstellung |

#### API/Database Field Changes:
| Old | New |
|-----|-----|
| buendel_verlauf | anfrage_verlauf |
| aktive_buendel | aktive_anfragen |
| gesamt_buendel | gesamt_anfragen |
| buendel_erstellt | anfragen_erstellt |
| buendel_gesendet | anfragen_gesendet |
| buendel_ids | anfrage_ids |

#### Event Names:
- `bundle.created` → `therapeutenanfrage.created`
- `bundle.sent` → `therapeutenanfrage.sent`
- `bundle.response_received` → `therapeutenanfrage.response_received`

## Phase 2: Data Model Updates

### 2.1 Patient Model Additions
```python
# New enum type
class Therapieverfahren(str, Enum):
    egal = "egal"
    Verhaltenstherapie = "Verhaltenstherapie" 
    tiefenpsychologisch_fundierte_Psychotherapie = "tiefenpsychologisch_fundierte_Psychotherapie"

# New fields
symptome = Column(Text)
erfahrung_mit_psychotherapie = Column(Text)
bevorzugtes_therapieverfahren = Column(ARRAY(SQLAlchemyEnum(Therapieverfahren)))  # PostgreSQL Array
bevorzugtes_therapeutenalter_min = Column(Integer)
bevorzugtes_therapeutenalter_max = Column(Integer)
```

### 2.2 Therapist Model Additions
```python
ueber_curavani_informiert = Column(Boolean, default=False)
```

### 2.3 Matching Models Updates
- `buendelgroesse` → `anfragegroesse`
- `position_im_buendel` → `position_in_anfrage`
- `buendel_patient_status` → `anfrage_patient_status`
- Constraint: `bundle_size_check` → `anfrage_size_check`
- All method names: bundle → anfrage

## Phase 3: Database Migration

### 3.1 Clean Database
```bash
docker-compose down -v
docker-compose up -d postgres
```

### 3.2 Create Migration: `002_terminology_and_model_updates.py`
```python
# Create new enum type for therapy procedures
op.execute("CREATE TYPE therapieverfahren AS ENUM ('egal', 'Verhaltenstherapie', 'tiefenpsychologisch_fundierte_Psychotherapie')")

# Rename columns and constraints
# Add new fields including:
op.add_column('patienten', sa.Column('bevorzugtes_therapieverfahren', 
              sa.ARRAY(sa.Enum(Therapieverfahren)), nullable=True), schema='patient_service')
```

## Phase 4: Configuration Updates

### 4.1 Update shared/config/settings.py
- `MAX_BUNDLE_SIZE` → `MAX_ANFRAGE_SIZE` (6)
- `MIN_BUNDLE_SIZE` → `MIN_ANFRAGE_SIZE` (1, was 3)
- Add: `PLZ_MATCH_DIGITS` (2)
- Add: `get_anfrage_config()` method

### 4.2 Update .env.example
Add all new configuration parameters with descriptions.

## Phase 5: Matching Service Complete Refactoring

### 5.1 File Structure Changes
- Rename: `bundle_creator.py` → `anfrage_creator.py`
- Rename: `api/bundle.py` → `api/anfrage.py`
- Delete: All PlacementRequest related files

### 5.2 Remove All Legacy Code
- Delete `PlacementRequest` model and imports
- Delete placement request API endpoints
- Remove ALL bundle terminology from code
- Delete these functions entirely:
  - `create_bundles_for_all_therapists()`
  - `apply_progressive_filtering()`
  - `calculate_patient_score()`
  - All `score_by_*()` functions
  - `analyze_therapist_preferences()`
- Clean up all unused imports

### 5.3 Implement New Core Function
```python
def create_therapeutenanfrage_for_therapist(db, therapist_id, plz_prefix):
    # PLZ filtering (hard constraint)
    # Apply ALL hard constraints (no scoring)
    # Support 1-6 patients
    # Order by creation date (oldest first)
```

### 5.4 Hard Constraints Implementation
Patient preferences (ALL must match or be null):
- Gender preference
- Age preference (min/max)
- Therapy procedures (at least one match)
- Group therapy compatibility

Therapist preferences (ALL must match or be null):
- Diagnosis preference
- Patient age (min/max)
- Gender preference

System constraints:
- Distance within patient's max travel distance
- Therapist not in patient's exclusion list

### 5.5 New API Endpoints
- `GET /api/therapeuten-zur-auswahl?plz_prefix=52` - Therapist selection
- `POST /api/therapeutenanfragen/erstellen-fuer-therapeut` - Create inquiry
- Remove: `/api/buendel/erstellen`, `/api/placement-requests`

### 5.6 Update Existing Endpoints
- All URLs: buendel → therapeutenanfragen
- All parameters: bundle → anfrage
- All responses: use new field names

### 5.7 Update Event Publishers
- Rename all functions: `publish_bundle_*` → `publish_anfrage_*`
- Update event types with new names
- Update payload field names

### 5.8 Update Service Layer
- Rename: `BundleService` → `AnfrageService`
- Update all method names and parameters
- Update log messages with new terminology

## Phase 6: Integration Tests

### 6.1 Test File: `tests/integration/test_new_matching_process.py`

### 6.2 Test Scenarios
- Therapist list with PLZ filter and sorting
- Create inquiry for manually selected therapist
- All hard criteria properly enforced
- Empty results handling
- Single patient inquiry (MIN=1)
- Response handling with new terminology

## Phase 7: API Documentation

### 7.1 Update API_REFERENCE.md
- Replace all bundle → therapeutenanfrage/inquiry
- Add new endpoints with examples
- Update field names (buendelgroesse → anfragegroesse, etc.)
- Document PLZ filtering parameter
- Update example responses

### 7.2 Document Hard Constraints
Clear documentation of all hard constraints and their logic.

## Phase 8: Email Template Updates (Deferred)
- Separate implementation
- Variable size support (1-6 patients)
- Reference format: A{anfrage_id}

## Phase 9: Final Cleanup

### 9.1 Code Review
- Verify all bundle references removed
- Check all imports are used
- Ensure consistent terminology

### 9.2 Documentation
- Update all README files
- Update inline comments
- Verify German field descriptions

## Execution Timeline

1. **Day 1**: ✅ Terminology unification
2. **Day 2**: Data models and migration
3. **Day 3**: Configuration and matching service refactoring
4. **Day 4**: Testing and API documentation
5. **Day 5**: Final validation and cleanup

## Success Criteria

- [x] Terminology updated in TERMINOLOGY.md
- [ ] Database migration with renamed fields
- [ ] New patient fields implemented (PostgreSQL ARRAY for therapieverfahren)
- [ ] New therapist field implemented
- [ ] Manual therapist selection with PLZ filter
- [ ] All hard constraints enforced (no soft scoring)
- [ ] Single patient inquiries allowed
- [ ] All legacy code removed
- [ ] Integration tests passing
- [ ] API documentation updated
- [ ] Events use new naming
- [ ] No regression in functionality

## Notes

- Direct replacement approach (no versioning)
- Email templates handled separately
- Development system (no data migration)
- German consistency throughout