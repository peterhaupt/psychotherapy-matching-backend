# Therapy Matching System - Implementation Plan

## Overview
Complete refactoring of the therapy matching system to implement the new manual therapist selection process with simplified matching logic.

## Phase 1: Terminology Unification

### 1.1 Update TERMINOLOGY.md ✅ COMPLETED

The TERMINOLOGY.md file has been updated with the following changes:

#### Core Terminology Changes:
- [x] **Bundle** → **Inquiry** (English)
- [x] **Bündel** → **Anfrage** (German)
- [x] **Bundle-Based System Terms** → **Therapist Inquiry System Terms**
- [x] **Bundle Email** → **Therapist Inquiry Email**

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

#### Count Fields Updated:
- Active Bundles → Active Inquiries (Aktive_anfragen)
- Total Bundles → Total Inquiries (Gesamt_anfragen)
- Bundles Created → Inquiries Created (Anfragen_erstellt)
- Bundles Sent → Inquiries Sent (Anfragen_gesendet)

#### Business Process Terms:
- Bundle Creation → Therapist Inquiry Creation
- Bundle Efficiency → Inquiry Efficiency
- Position in Bundle → Position in Inquiry

### 1.2 Code Terminology Updates
- [ ] Rename database fields:
  - `buendelgroesse` → `anfragegroesse`
  - `buendel_patient_status` → `anfrage_patient_status`
  - Any other "buendel" references
- [ ] Update API endpoints:
  - `/api/buendel/erstellen` → `/api/therapeutenanfragen/erstellen`
- [ ] Update all variable names, comments, and docstrings
- [ ] Update event names (e.g., `bundle.created` → `therapeutenanfrage.created`)

## Phase 2: Data Model Updates

### 2.1 Patient Model Additions
```python
# New fields for patient_service/models/patient.py

# Add to enum definitions
class Therapieverfahren(str, Enum):
    egal = "egal"
    Verhaltenstherapie = "Verhaltenstherapie" 
    tiefenpsychologisch_fundierte_Psychotherapie = "tiefenpsychologisch_fundierte_Psychotherapie"

# Add to Patient model under Medical Information section
symptome = Column(Text)  # New field
erfahrung_mit_psychotherapie = Column(Text)  # New field

# Add to Patient model under preferences
bevorzugtes_therapieverfahren = Column(JSONB)  # Array of Therapieverfahren
bevorzugtes_therapeutenalter_min = Column(Integer)
bevorzugtes_therapeutenalter_max = Column(Integer)
```

### 2.2 Therapist Model Additions
```python
# Add to therapist_service/models/therapist.py
ueber_curavani_informiert = Column(Boolean, default=False)
```

### 2.3 Update Matching Models
- [ ] Rename all "bundle" references to "therapeutenanfrage" in model names
- [ ] Update relationship names and foreign keys

## Phase 3: Database Migration

### 3.1 Clean Database
```bash
# Commands to execute
docker-compose down -v  # Remove volumes
docker-compose up -d postgres  # Start only postgres
```

### 3.2 Create New Alembic Migration
- [ ] Delete all existing migration files
- [ ] Create new initial migration with all updated models
- [ ] Include all new fields and renamed fields
- [ ] Ensure all enum types use new terminology

## Phase 4: Configuration Updates

### 4.1 Add to shared/config/settings.py
```python
# Matching configuration
MAX_ANFRAGE_SIZE = int(os.getenv('MAX_ANFRAGE_SIZE', '6'))
MIN_ANFRAGE_SIZE = int(os.getenv('MIN_ANFRAGE_SIZE', '1'))  # Now 1 instead of 3
COOLING_PERIOD_WEEKS = int(os.getenv('COOLING_PERIOD_WEEKS', '4'))
FOLLOW_UP_DAYS = int(os.getenv('FOLLOW_UP_DAYS', '7'))
PLZ_MATCH_DIGITS = int(os.getenv('PLZ_MATCH_DIGITS', '2'))  # New parameter
```

### 4.2 Update .env.example
- [ ] Add all new configuration parameters with defaults
- [ ] Document each parameter's purpose

## Phase 5: Matching Service Refactoring

### 5.1 Delete Obsolete Code
Remove from `matching_service/algorithms/bundle_creator.py`:
- [ ] `create_bundles_for_all_therapists()` - no more batch processing
- [ ] `apply_progressive_filtering()` - no scoring needed
- [ ] `calculate_patient_score()` - only hard criteria now
- [ ] All `score_by_*` functions
- [ ] `analyze_therapist_preferences()` - not needed

### 5.2 Implement New Algorithm
```python
# New main function in bundle_creator.py
def create_therapeutenanfrage_for_therapist(
    db: Session,
    therapist_id: int, 
    plz_prefix: str
) -> Optional[Therapeutenanfrage]:
    """
    Create a Therapeutenanfrage for a specific therapist with PLZ filtering.
    
    Args:
        db: Database session
        therapist_id: Selected therapist
        plz_prefix: PLZ prefix to filter patients (e.g., "52")
    """
    # Implementation following the new process
```

### 5.3 Update Hard Constraint Functions
- [ ] `check_distance_constraint()` - keep as is
- [ ] `check_exclusion_constraint()` - keep as is
- [ ] Add `check_therapieverfahren_preference()` - new constraint
- [ ] Add `check_therapist_age_preference()` - new constraint
- [ ] Update `check_gender_preference()` - ensure it's a hard constraint

### 5.4 New API Endpoints
```python
# In matching_service/api/bundle.py

# Get therapists for manual selection
GET /api/therapeuten-zur-auswahl?plz_prefix=52
Response: Sorted list of eligible therapists

# Create Therapeutenanfrage for specific therapist
POST /api/therapeutenanfragen/erstellen-fuer-therapeut
Body: {
    "therapist_id": 123,
    "plz_prefix": "52"
}
```

### 5.5 Update Existing Endpoints
- [ ] Remove batch creation endpoints
- [ ] Update response handling for single-patient Therapeutenanfragen
- [ ] Add "already_matched" status handling

## Phase 6: Integration Tests

### 6.1 Create Test File
`tests/integration/test_new_matching_process.py`

### 6.2 Test Scenarios
```python
def test_therapist_list_with_plz_filter():
    """Test getting sorted therapist list with PLZ filter"""

def test_create_anfrage_manual_selection():
    """Test creating Therapeutenanfrage for manually selected therapist"""

def test_hard_criteria_filtering():
    """Test all hard criteria are properly enforced"""

def test_empty_results_handling():
    """Test when no patients match criteria"""

def test_single_patient_anfrage():
    """Test creating Anfrage with just 1 patient"""

def test_patient_already_matched_handling():
    """Test marking patients as already matched"""

def test_cooling_period_enforcement():
    """Test therapists in cooling period are excluded"""
```

## Phase 7: API Documentation

### 7.1 Update API_REFERENCE.md
- [ ] Document new endpoints for therapist selection
- [ ] Update all "bundle" references to "therapeutenanfrage"
- [ ] Document new query parameters (plz_prefix)
- [ ] Add examples for new manual process

### 7.2 Update Field Documentation
- [ ] Document new patient fields
- [ ] Document new therapist fields
- [ ] Update enum documentation

## Phase 8: Email Template Updates (Deferred)
- To be discussed and implemented separately
- Must handle variable size (1-6 patients)
- Reference format decision pending

## Phase 9: Testing & Validation

### 9.1 Unit Tests
- [ ] Update all existing tests for new terminology
- [ ] Add tests for new constraint functions
- [ ] Add tests for PLZ matching logic

### 9.2 End-to-End Testing
- [ ] Manual therapist selection flow
- [ ] Therapeutenanfrage creation with various sizes
- [ ] Response handling
- [ ] Cooling period verification

## Phase 10: Cleanup

### 10.1 Remove Legacy Code
- [ ] Delete old bundle creation algorithms
- [ ] Remove unused imports
- [ ] Clean up obsolete event handlers

### 10.2 Documentation Updates
- [ ] Update all documentation files
- [ ] Update code comments
- [ ] Update README files

## Execution Order

1. **Day 1**: ~~Terminology unification (Phase 1)~~ ✅ COMPLETED
2. **Day 2**: Data model updates and migration (Phases 2-3)
3. **Day 3**: Configuration and matching service refactoring (Phases 4-5)
4. **Day 4**: Testing implementation (Phase 6)
5. **Day 5**: Documentation and cleanup (Phases 7, 9-10)

## Success Criteria

- [x] All "Bündel" references replaced with "Therapeutenanfrage" in TERMINOLOGY.md
- [ ] New patient and therapist fields implemented
- [ ] Manual therapist selection working with PLZ filter
- [ ] All hard constraints properly enforced
- [ ] Configuration parameters centralized
- [ ] Integration tests passing
- [ ] API documentation updated
- [ ] No regression in existing functionality

## Notes

- Email rewrite (Phase 8) to be discussed separately
- This is a development system - no data migration needed
- No API versioning - direct replacement
- Feature flags not needed - hard cutover
- TERMINOLOGY.md update completed - old terminology file can be safely deleted