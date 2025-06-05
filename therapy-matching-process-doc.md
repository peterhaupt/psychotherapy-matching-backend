# Therapy Matching Platform - Business Process Documentation

## Executive Summary

This document outlines the business processes for the Psychotherapy Matching Platform, incorporating refined terminology and process flows. The platform manages **Patient Searches** (Platzsuche) - long-running processes to find therapy spots for patients - and **Therapist Inquiries** (Therapeutenanfrage) - specific requests sent to therapists asking if they can treat one or more patients.

## Key Terminology

### Patient Search (Platzsuche)
- **Definition**: The ongoing process of finding a therapy spot for a patient
- **Lifecycle**: Starts when patient registers, ends when they successfully find a therapist
- **Constraint**: One active search per patient at a time
- **Duration**: Weeks to months until successful placement
- **Contains**: Patient preferences, exclusions, search status, history

### Therapist Inquiry (Therapeutenanfrage)
- **Definition**: A specific request sent to a therapist asking if they can treat one or more patients
- **Content**: Multiple patients bundled together (minimum configurable, starting with 3)
- **Lifecycle**: Created, sent, awaiting response, responded
- **Duration**: Days to weeks
- **Response Types**: Accepted (for specific patients), rejected, no response

## Current Implementation Status

### What Exists
- ✅ Microservice architecture with Patient, Therapist, Matching, Communication, and Geocoding services
- ✅ Basic matching algorithm that filters by distance, gender preference, and exclusions
- ✅ Email batching system (groups up to 5 patients per email)
- ✅ Automatic phone call scheduling (7 days after unanswered emails)
- ✅ Contact frequency limits (currently 1 week, needs change to 1 month)
- ✅ `potentially_available` field on therapists
- ✅ Daily scraping from 116117.de for therapist data

### Key Gaps
- ❌ No distinction between Patient Search and Therapist Inquiry entities
- ❌ No regional accumulation logic (3-day wait for bundling)
- ❌ No wave-based outreach management
- ❌ Contact frequency is 1 week instead of 1 month
- ❌ No tracking of unanswered inquiry thresholds
- ❌ No visibility into search statistics per patient

## Process Flow: Patient Search Management

### 1. Patient Search Creation (Platzsuche Erstellung)

**When Created:**
- Patient registers and needs therapy placement
- Previous search was closed (successful or abandoned)

**What's Captured:**
1. **Core Preferences** (from patient model):
   - Gender preference (`bevorzugtes_therapeutengeschlecht`)
   - Open for group therapy (`offen_fuer_gruppentherapie`)
   - Maximum travel distance (`raeumliche_verfuegbarkeit`)
   - Travel mode - car or public transit (`verkehrsmittel`)

2. **Manual Exclusions** (added during search creation):
   - Specific therapist exclusions (bad experiences, family relations)
   - Stored in `ausgeschlossene_therapeuten`

3. **Search Metadata**:
   - Creation date
   - Current status
   - Statistics (therapists contacted, responses received)

### 2. Regional Accumulation (Regionale Sammlung)

**Purpose**: Bundle multiple patient searches before contacting therapists

**Process:**
1. **Region Definition**: Patients are grouped by geographic proximity
   - "Same region" = overlapping potential therapist pools
   - Based on patient locations and their max travel distances

2. **Accumulation Period**: 
   - Wait up to 3 days to collect patients in same region
   - Configurable minimum bundle size (initially 3 patients)
   - Can be overridden for urgent cases

3. **Bundle Creation**:
   - Group patient searches that share potential therapists
   - Prepare for wave-based outreach

### 3. Wave-Based Therapist Selection (Wellenbasierte Therapeutenauswahl)

**Purpose**: Avoid blocking entire regions while maximizing success chances

**Wave Strategy:**
1. **Initial Pool**: Identify all eligible therapists for the patient bundle
   - Filter by distance, gender preference, exclusions
   - Check monthly contact limit (not contacted in last 30 days)

2. **Prioritization**:
   - First: `potentially_available = true` therapists
   - Then: Sort by distance (closest first)
   - Consider other factors (TBD in future discussion)

3. **Wave Size**: 
   - Select subset (e.g., 20 out of 100 eligible)
   - Configurable per region/situation
   - Ensures other patients can still access therapists in region

4. **Wave Triggers**:
   - First wave: Sent after accumulation period
   - Next waves: Triggered when unanswered inquiries drop below threshold
   - Configurable threshold (e.g., 5 pending inquiries)

### 4. Therapist Inquiry Creation (Therapeutenanfrage Erstellung)

**For Each Selected Therapist:**
1. Create single Therapist Inquiry containing:
   - Multiple patient searches (up to 5)
   - Inquiry metadata (date, wave number)
   - Expected response tracking

2. **Contact Rules**:
   - Global limit: One contact per therapist per month
   - Applies across all patients and inquiries
   - Prevents therapist spam

### 5. Communication Process (Kommunikationsprozess)

**Handled by Communication Service:**

1. **Email Phase**:
   - Send bundled inquiry email
   - Template includes multiple patient summaries
   - Track send date and delivery

2. **Follow-up Phase** (if no response):
   - After 7 days: Schedule phone call
   - Phone call covers same patient bundle
   - Document call outcome

3. **Response Types**:
   - **Global Rejection**: "No capacity for any patients"
   - **Selective Acceptance**: "Can see patients 2 and 4"
   - **Information Request**: "Need more details about patient 3"
   - **No Response**: Triggers follow-up

### 6. Response Processing (Antwortverarbeitung)

**Per Therapist Inquiry:**
1. Record response for each included patient
2. Update Patient Search statistics
3. Handle accepted patients:
   - Schedule patient-therapist meeting
   - Mark search as "pending meeting"
4. Handle rejections:
   - Update statistics
   - Patient remains in pool for next wave

### 7. Wave Management (Wellenverwaltung)

**Continuous Process:**
1. Monitor active inquiries per patient bundle
2. When below threshold (e.g., < 5 pending):
   - Select next wave of therapists
   - Create new inquiries
   - Respect monthly contact limits

3. **Statistics Tracking**:
   - "Contacted 30/100 potential therapists"
   - "15 rejected, 10 no response, 5 pending"
   - Visible at Patient Search level

### 8. Search Completion (Platzsuche Abschluss)

**Successful Completion:**
1. Therapist accepts patient
2. Patient-therapist meeting successful
3. Patient Search marked "completed"
4. Historical data retained

**Abandonment:**
- Patient no longer needs placement
- Search marked "abandoned"
- Reason documented

## Data Model Requirements

### Patient Search (Platzsuche)
```
- id
- patient_id (FK)
- status: active|pending_meeting|completed|abandoned
- created_at
- completed_at
- total_therapists_available
- total_therapists_contacted
- total_accepted
- total_rejected
- total_no_response
- current_wave
- notes
```

### Therapist Inquiry (Therapeutenanfrage)
```
- id
- therapist_id (FK)
- wave_number
- sent_date
- response_date
- response_type: accepted|rejected|no_response|partial_acceptance
- communication_method: email|phone
- included_patient_searches: [patient_search_id, ...]
- individual_responses: {patient_search_id: accepted|rejected|pending}
```

### Regional Bundle (Regionales Bündel)
```
- id
- region_identifier
- created_at
- patient_searches: [patient_search_id, ...]
- status: accumulating|ready|processing
- target_size
- current_size
```

## Configuration Parameters

### Global Settings
- **Minimum Bundle Size**: 3 patients (configurable)
- **Accumulation Wait Time**: 3 days (configurable)
- **Wave Size**: 20 therapists (configurable)
- **Pending Inquiry Threshold**: 5 (configurable)
- **Contact Frequency Limit**: 30 days (configurable)
- **Email to Phone Delay**: 7 days (existing)

### Per-Region Overrides
- Can adjust bundle size based on patient density
- Can modify wave size based on therapist availability
- Emergency overrides for urgent cases

## Implementation Priorities

### Phase 1: Core Process Changes
1. **Implement Patient Search entity**
   - Track overall search progress
   - Maintain statistics

2. **Implement Therapist Inquiry entity**
   - Replace/extend current PlacementRequest
   - Support bundled patients

3. **Regional Accumulation Logic**
   - Geographic proximity calculation
   - Configurable wait times and thresholds

4. **Wave Management**
   - Therapist pool filtering
   - Wave selection algorithm
   - Trigger monitoring

5. **Update Contact Frequency**
   - Change from 1 week to 1 month
   - Global therapist tracking

### Phase 2: Enhanced Features
1. Response tracking and statistics
2. Detailed status visibility
3. Manual override capabilities
4. Advanced prioritization factors

### Phase 3: Optimization
1. Machine learning for success prediction
2. Dynamic threshold adjustment
3. Regional pattern analysis

## Open Questions for Future Discussion

1. **Prioritization Factors**: Beyond `potentially_available` and distance, what additional factors should influence therapist selection order?

2. **Regional Boundaries**: Should regions be fixed (PLZ-based) or dynamic (based on current patient clusters)?

3. **Urgent Cases**: How do we define and handle urgent patient cases that can't wait for accumulation?

4. **Partial Responses**: How do we handle therapists who accept some but not all patients in a bundle?

5. **Quality Metrics**: What KPIs should we track to optimize the matching process?

## API Changes Required

### New Endpoints Needed
```
# Patient Search Management
POST   /api/patient-searches
GET    /api/patient-searches/{id}
PUT    /api/patient-searches/{id}/status
GET    /api/patient-searches/{id}/statistics

# Regional Bundle Management  
GET    /api/regional-bundles/pending
POST   /api/regional-bundles/{id}/trigger-wave

# Therapist Inquiry Management
POST   /api/therapist-inquiries/bulk
GET    /api/therapist-inquiries?patient_search_id=X
PUT    /api/therapist-inquiries/{id}/response

# Wave Management
GET    /api/waves/next-candidates?bundle_id=X
POST   /api/waves/create
```

### Modified Endpoints
- Deprecate current `/api/placement-requests` in favor of new structure
- Update `/api/therapists` to include last contact date
- Enhance `/api/patients/{id}/available-therapists` with wave information

## Conclusion

The refined process clearly separates the long-running Patient Search (Platzsuche) from the short-lived Therapist Inquiries (Therapeutenanfrage). This enables better tracking, intelligent bundling, and respectful therapist communication while maximizing the chances of successful placements. The wave-based approach prevents regional blocking while the accumulation strategy ensures efficient use of therapist goodwill.