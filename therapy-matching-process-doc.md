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

### 3. Contact Management & Cooling Periods

#### 3.1 Cooling Period Rules
- **Trigger**: Cooling period starts after ANY response from therapist (email reply or successful phone contact)
- **Duration**: 4 weeks (configurable for future adjustments)
- **Scope**: Applies system-wide - therapist cannot be contacted for ANY patient during cooling period
- **Storage**: Tracked in therapist record as `next_contactable_date`

#### 3.2 Contact Request Management
- **Additive requests**: Staff can add contact requests at any time (e.g., "add 25 more contacts")
- **No fulfillment requirement**: Requests don't need to be "completed" - they simply expand the pool
- **Concurrent processing**: Some contacts may still be pending (awaiting email response or phone scheduling) while new requests are added

### 4. Bundle Creation & Optimization

#### 4.1 Manual Bundle Creation Process
- **Trigger**: Staff manually initiates bundle creation
- **Timing**: Flexible based on operational needs and available patient pools
- **Concurrent bundles**: Patients MUST appear in multiple bundles to accelerate placement

#### 4.2 Bundle Composition Algorithm

The algorithm uses **progressive filtering** with clear priorities:

##### Step 1: Initial Pool
- All active therapists
- Exclude those in cooling period (`next_contactable_date > today`)
- Exclude inactive/blocked therapists

##### Step 2: Hard Constraints (MUST be satisfied)
For each therapist, only include patients who:
- Are within patient's maximum travel distance
- Are NOT in patient's exclusion list
- Match patient's gender preference (if specified)

##### Step 3: Progressive Filtering by Priority
Apply filters in order until reaching target therapist count:

1. **Availability Compatibility** (when known)
   - If therapist schedule known: Include only if overlap exists
   - If unknown: Include all (therapist self-assesses from patient schedules)

2. **Therapist Preferences**
   - Diagnosis preference match
   - Age preference match
   - Gender preference match
   - Group therapy preference match (soft constraint for patients)

3. **Patient Waiting Time**
   - Sort by longest waiting patients first

4. **Geographic Proximity**
   - Sort by average distance of bundle patients

##### Step 4: Bundle Size per Therapist
- Select 3-6 patients per therapist
- Prioritize longest-waiting eligible patients

### 5. Response Handling

#### 5.1 Response Types
1. **Full Acceptance** (rare): All patients in bundle accepted
2. **Partial Acceptance** (common): 1-2 patients accepted from bundle
3. **Full Rejection** (common): All patients rejected
4. **No Response**: Trigger phone follow-up after 7 days

#### 5.2 Processing Responses
- **Accepted patients**: Remove from active search, schedule initial sessions
- **Rejected patients**: 
  - Remain in active search
  - Can be re-bundled to same therapist after cooling period
  - Track rejection for analytics
- **Multiple acceptances**: If patient accepted by multiple therapists, assign to first responder and offer alternatives to other therapists

### 6. Parallel Processing & Conflict Resolution

#### 6.1 Multiple Bundle Membership
- **Requirement**: Patients MUST be in multiple concurrent bundles
- **Rationale**: Accelerates placement timeline
- **Risk management**: Multiple acceptances are positive (shows system effectiveness)

#### 6.2 Conflict Resolution
When multiple therapists accept same patient:
1. Assign patient to first responding therapist
2. Contact other accepting therapists immediately
3. Offer alternative patients from their bundle or other available patients
4. Maintain positive relationship with all accepting therapists

### 7. Manual Interventions

**"Changed mind" scenario**:
- Therapist initially rejects but later calls with sudden opening
- Staff manually selects appropriate patient from active searches
- Assignment made outside normal bundle process
- System tracks these manual placements

**Dynamic exclusions**:
- Patient has bad experience with therapist during initial sessions
- Add therapist to exclusion list in Platzsuche
- Prevents future contact for this patient

### 8. Success Tracking

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
- therapist_gender_preference: male|female|any (HARD constraint)
- group_therapy_preference: boolean (SOFT constraint)
```

### Therapist (Enhanced)
```
- id
- ... (existing fields)
- next_contactable_date: date (cooling period enforcement)
- last_contact_date: date
- preferred_diagnoses: [ICD-10 codes]
- age_min: integer
- age_max: integer
- gender_preference: male|female|any
- group_therapy_preference: boolean
- phone_availability: JSON
- working_hours: JSON (when known)
```

### Platzsuche (Patient Search)
```
- id
- patient_id (FK)
- status: active|in_sessions|successful|abandoned
- created_at
- success_date
- excluded_therapists: [therapist_id, ...]
- total_requested_contacts: integer (sum of all requests)
```

### PlatzucheContactRequest
```
- id
- platzsuche_id (FK)
- requested_count: integer
- requested_date: datetime
- created_by: user_id
```

### Therapeutenanfrage (Therapist Inquiry)
```
- id
- therapist_id (FK)
- created_date
- sent_date
- sent_method: email|phone
- response_date
- response_type: accepted|rejected|no_response|partial
- bundle_size: integer
- accepted_count: integer
- staff_notes
```

### TherapeutAnfragePatient (Bundle Composition)
```
- therapeutenanfrage_id (FK)
- platzsuche_id (FK)
- patient_id (FK)
- position_in_bundle: integer
- status: pending|accepted|rejected
- outcome_notes: text
```

## Operational Parameters

### Configurable Settings
- **Bundle size**: 3-6 patients (configurable per system)
- **Response wait time**: 7 days before phone follow-up
- **Cooling period**: 4 weeks after any response (configurable)
- **Minimum patient availability**: 20 hours/week
- **Success measurement**: After 2 initial sessions

### Manual Override Capabilities
- Direct assignment when therapist calls with opening
- Bundle size exceptions
- Cooling period exceptions (documented with reason)
- Exclusion list management

## Implementation Architecture

### Service Responsibilities

#### Matching Service
- Stores therapist preferences
- Implements bundle creation algorithm
- Creates Therapeutenanfrage records
- Tracks bundle composition
- Enforces cooling periods via `next_contactable_date`

#### Communication Service
- Sends individual emails (NO bundle logic)
- Schedules phone calls
- Records response dates
- Notifies matching service of responses

#### Process Flow
1. Staff triggers bundle creation in Matching Service
2. Matching Service creates optimal bundles
3. Matching Service creates Therapeutenanfrage records
4. Matching Service calls Communication Service to send emails
5. Communication Service notifies Matching Service of responses
6. Matching Service updates cooling periods

## Key Business Metrics

### Success Metrics
- **Placement speed**: Days from registration to successful placement (target: weeks, not months)
- **Therapist acceptance rate**: % of patients accepted from bundles
- **Patient show rate**: % attending initial sessions
- **Conflict rate**: % of patients accepted by multiple therapists (positive indicator)

### Operational Metrics
- **Bundle efficiency**: Average accepts per bundle
- **Response rate**: % of therapists responding within 7 days
- **Cooling compliance**: % of contacts respecting cooling periods
- **Parallel search effectiveness**: Average concurrent bundles per patient

## Competitive Advantage

Curavani succeeds by solving both sides' core problems:

**For Therapists**:
- Zero effort patient acquisition
- Pre-qualified, insurance-ready patients
- Preference-matched bundles
- Clear availability information
- Predictable contact frequency (cooling periods)

**For Patients**:
- Placement within weeks through parallel search
- Higher acceptance rates through intelligent matching
- Professional advocacy and follow-up
- Access to therapists who rarely advertise openings

This creates a virtuous cycle where therapists prefer Curavani patients, leading to more available spots and faster placements, justifying the private payment model.