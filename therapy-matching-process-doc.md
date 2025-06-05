# Therapy Matching Platform - Business Process Documentation

## Executive Summary

This document outlines the business processes for the Psychotherapy Matching Platform (Curavani), which operates in the German public healthcare market. The platform's core value proposition is:

1. **For Patients**: Get therapy spots within **weeks** (not months) - this is what they pay for
2. **For Therapists**: Eliminate administrative burden through pre-qualified, bundled patient requests
3. **For Curavani**: Must become therapists' preferred channel to access sufficient spots to deliver this speed

## Business Context: German Public Healthcare Market

### Therapist Pain Points
1. **Unclarified patient availability** - Coordinating sessions becomes extremely difficult
2. **Insufficient weekly availability** - Patients with only few hours/week are hard to schedule
3. **Missing insurance information** - Unclear coverage status
4. **Missing diagnosis** - No proper ICD-10 diagnosis from psychotherapeutic consultation
5. **2-year rule violations** - Insurance complications if less than 2 years since last therapy
6. **Missing patient age** - Important for therapist specialization
7. **Verbose, unfocused problem descriptions** - Time-wasting communication
8. **Unreliable patients** - Last-minute cancellations or no-shows

### Current Therapist Behavior
- Work "first come, first served" when spots open
- Avoid waiting lists (too much effort for 6-12 month wait times)
- Many patients lose interest after 6 months waiting

## Curavani's Value Proposition

### Patient Pre-Qualification
1. **Financial commitment**: Patients pay Curavani privately (not insurance-covered) = motivation filter
2. **Recent diagnosis verification**: Confirmed ICD-10 diagnosis from psychotherapeutic consultation
3. **Availability check**: Minimum 20 hours/week availability required
4. **2-year rule compliance**: Verify last therapy ended 2+ years ago
5. **Additional profiling**: Therapy goals and motivation assessment (if therapists want it)

### Therapist Benefits
1. **Insurance-ready patients**: All formal requirements pre-checked
2. **Bundled communication**: One email/call instead of 5-6 separate patient contacts
3. **Preference matching**:
   - Preferred diagnoses (e.g., primarily depression)
   - Age groups (e.g., only elderly)
   - Gender (e.g., only women)
   - Group therapy openness (better insurance reimbursement)
4. **Availability information**: Patient schedules included for therapist self-assessment

## Key Terminology

### Patient Search (Platzsuche)
- **Definition**: The ongoing process of finding a therapy spot for a patient
- **Duration**: Weeks until successful placement (target benchmark)
- **Success**: Patient agrees to therapist after 1-2 initial sessions
- **Contains**: Search history, therapist exclusions, contact tracking

### Therapist Inquiry (Therapeutenanfrage)
- **Definition**: A bundled request to ONE therapist containing multiple patient options
- **Size**: 3-6 patients per bundle (configurable)
- **Purpose**: Give therapist choice while minimizing their effort
- **Response time**: Expected within 1 week
- **Typical outcome**: Therapist accepts 1-2 patients from bundle

## Process Flow

### 1. Patient Onboarding & Validation

**Pre-qualification checks**:
1. Payment received (private payment)
2. Recent diagnosis verified (ICD-10)
3. Insurance eligibility confirmed
4. 2-year rule compliance checked
5. Weekly availability ≥20 hours confirmed
6. Detailed availability schedule captured (hourly for each day)

**Data captured in Patient record**:
- Demographics (including age)
- Diagnosis details
- Insurance information
- Previous therapy history
- Availability matrix (e.g., Mon 9-13, Tue 14-18, etc.)
- **Maximum travel distance** (in km)
- **Travel mode preference** (car/public transport)
- Preferences (therapist gender, group therapy openness)

### 2. Therapist Profiling

**Information gathering** (via phone/personal contact):
- Preferred diagnoses
- Age preferences
- Gender preferences
- Group vs. individual therapy preference
- Working hours (detailed weekly schedule when available)
- Special requirements
- Phone availability windows (1-3 hours per week typically)

**Continuous updates**:
- Preferences learned from acceptance/rejection patterns
- Schedule changes tracked over time
- "Potentially available" status maintained

### 3. Optimized Bundle Creation Workflow

#### 3.1 Patient Search (Platzsuche) Management
**Purpose**: Define patient-specific search parameters and track progress

**Actions**:
- Create Platzsuche for new patient
- **Manage exclusions**: Add/remove specific therapists patient doesn't want
- **Request contacts**: "Request 25 additional therapist contacts"

**Display (Read-only)**:
- Total therapists requested: 45
- Total therapists contacted: 25
- Pending requests: 20
- List of contacted therapists (with date, response status)

#### 3.2 Therapist Inquiry (Therapeutenanfrage) Optimization
**Purpose**: Globally optimize which therapists to contact and how to bundle patients

**Process**:
1. **Collect requests** from all active Platzsuche:
   - Patient A: needs 25 more contacts
   - Patient B: needs 15 more contacts
   - Patient C: needs 20 more contacts

2. **Find eligible therapists** for each patient:
   - Within patient's maximum travel distance
   - Not in patient's exclusion list
   - Not contacted too recently (30-day limit)
   - Match preferences where known

3. **Create optimal bundles**:
   - System proposes bundles maximizing acceptance likelihood
   - Staff reviews proposed bundles
   - Can send immediately or wait for better bundling opportunities

4. **Track fulfillment**:
   - Update each Platzsuche with contacts made
   - Monitor response rates

### 4. Bundle Composition Priorities

The system prioritizes bundle composition factors as follows:

1. **Availability Compatibility** (HIGHEST PRIORITY)
   - Initially assume therapists work all week (unknown schedules)
   - Include patient availability in emails for therapist self-assessment
   - As we learn therapist schedules, improve matching

2. **Therapist Preferences** 
   - Preferred diagnoses
   - Age preferences
   - Gender preferences
   - Group therapy preference

3. **Patient Waiting Time**
   - Prioritize patients who have been waiting longer
   - Ensure fairness in the queue

4. **Geographic Proximity**
   - While all patients in bundle must be within travel distance
   - Prefer shorter distances when possible

### 5. Contact Management

**Initial contact**:
- Email with bundled patient summaries
- Clear, structured format showing:
  - Patient diagnosis
  - Age and gender
  - Availability schedule
  - Travel distance to therapist
  - Group therapy openness
- All pre-qualification confirmed

**Follow-up** (if no response after 7 days):
- Phone call scheduled within therapist's availability window (1-3 hours/week)
- Same bundle discussed
- Outcome documented

**Contact frequency limit**:
- Maximum 1 contact per therapist per month (system-wide)
- Tracked globally across all patients

### 6. Response Processing

**Response types**:
1. **Acceptance** (most common: 1-2 patients from bundle):
   - Schedule initial sessions
   - Track which specific patients accepted
   - Other patients remain active in their Platzsuche

2. **Rejection** (all patients):
   - Document reason if given
   - Track rejection per patient-therapist pair
   - Patients remain active for future bundles

3. **Partial acceptance**:
   - Process accepted patients
   - Non-accepted patients continue search

4. **No response**:
   - Trigger phone follow-up after 7 days

### 7. Parallel Processing

- **Multiple therapists contacted simultaneously** for each patient
- A patient can appear in multiple bundles sent to different therapists
- First acceptance wins
- Other pending requests cancelled upon successful placement

### 8. Manual Interventions

**"Changed mind" scenario**:
- Therapist initially rejects but later calls with sudden opening
- Staff manually selects appropriate patient from active searches
- Assignment made outside normal bundle process
- System tracks these manual placements

**Dynamic exclusions**:
- Patient has bad experience with therapist during initial sessions
- Add therapist to exclusion list in Platzsuche
- Prevents future contact for this patient

### 9. Success Tracking

**Placement success defined as**:
- Patient attends initial 1-2 sessions
- Patient agrees to continue with therapist
- Formal therapy begins

**If patient doesn't continue**:
- Add therapist to exclusion list
- Continue search with new therapist contacts
- Track as "attempted placement"

## Data Model Requirements

### Patient (Enhanced)
```
- id
- ... (existing fields)
- max_travel_distance_km: integer
- travel_mode: car|public_transport
- availability_schedule: JSON
```

### Platzsuche (Patient Search)
```
- id
- patient_id (FK)
- status: active|in_sessions|successful|abandoned
- created_at
- success_date
- excluded_therapists: [therapist_id, ...]
- total_requested_contacts: integer
- total_fulfilled_contacts: integer
```

### PlatzucheContactRequest
```
- id
- platzsuche_id (FK)
- requested_count: integer
- requested_date: datetime
- fulfilled_count: integer
- status: pending|partial|complete
```

### Therapeutenanfrage (Therapist Inquiry)
```
- id
- therapist_id (FK)
- sent_date
- sent_method: email|phone
- response_date
- response_type: accepted|rejected|no_response|partial
- bundle_size: integer
- staff_notes
```

### TherapeutAnfragePatient (Bundle Composition)
```
- therapeutenanfrage_id (FK)
- platzsuche_id (FK)
- patient_id (FK)
- status: pending|accepted|rejected
- counted_towards_request: boolean
```

### Therapist Preferences
```
- therapist_id (FK)
- preferred_diagnoses: [ICD-10 codes]
- age_min
- age_max
- gender_preference: male|female|any
- group_therapy_preference: boolean
- phone_availability: JSON (day -> time slots)
- working_hours: JSON (when known)
- last_contact_date
- last_updated
- notes
```

## Operational Parameters

### Configurable Settings
- **Bundle size**: 3-6 patients (configurable per system)
- **Response wait time**: 7 days before phone follow-up
- **Contact frequency**: 30 days minimum between contacts to same therapist
- **Minimum patient availability**: 20 hours/week
- **Success measurement**: After 2 initial sessions

### Manual Override Capabilities
- Direct assignment when therapist calls with opening
- Bundle size exceptions
- Contact frequency exceptions (documented)
- Exclusion list management

## Implementation Notes

### Optimization Algorithm
The algorithm for how Therapeutenanfrage selects optimal therapists from the pool of requests needs to be discussed and specified in detail in a separate session. Key considerations will include:
- Maximizing bundle quality
- Balancing fairness across patients
- Respecting all constraints
- Learning from historical acceptance patterns

### User Interface Requirements

**Platzsuche Interface**:
- Simple request mechanism: "Request X additional contacts"
- Clear exclusion list management
- Read-only view of contact history
- Progress indicators

**Therapeutenanfrage Interface**:
- Bundle preview and editing
- Batch operations for efficiency
- Clear constraint visualization
- Response tracking dashboard

## Key Business Metrics

### Success Metrics
- **Placement speed**: Days from registration to successful placement (target: weeks, not months)
- **Therapist acceptance rate**: % of patients accepted from bundles
- **Patient show rate**: % attending initial sessions
- **Therapist retention**: % preferring Curavani over direct inquiries

### Operational Metrics
- **Bundle efficiency**: Average accepts per bundle
- **Response rate**: % of therapists responding within 7 days
- **Contact fulfillment**: % of requested contacts successfully made
- **Optimization effectiveness**: Actual vs. optimal bundle composition

## Competitive Advantage

Curavani succeeds by solving both sides' core problems:

**For Therapists**:
- Zero effort patient acquisition
- Pre-qualified, insurance-ready patients
- Preference-matched bundles
- Clear availability information
- No time wasted on unmotivated patients

**For Patients**:
- Placement within weeks, not months
- Higher acceptance rates through intelligent matching
- Professional advocacy and follow-up
- No need to contact dozens of therapists individually

This creates a virtuous cycle where therapists prefer Curavani patients, leading to more available spots and faster placements, justifying the private payment model.