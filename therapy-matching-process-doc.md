# Therapy Matching Platform - Business Process Documentation

## Executive Summary

This document outlines the business processes for the Psychotherapy Matching Platform (Curavani), which operates in the German public healthcare market. The platform's core value proposition is to become therapists' preferred channel for patient placement by:

1. **For Patients**: Dramatically reducing waiting times for therapy spots
2. **For Therapists**: Eliminating administrative burden through pre-qualified, bundled patient requests
3. **For Curavani**: Becoming the trusted intermediary that therapists prefer over random patient inquiries

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
   - Specific diagnoses (e.g., only depression)
   - Age groups (e.g., only elderly)
   - Gender (e.g., only women)
   - Group therapy openness (better insurance reimbursement)
4. **Availability matching**: Patients pre-filtered for therapist's working hours

## Key Terminology (Refined)

### Patient Search (Platzsuche)
- **Definition**: The ongoing process of finding a therapy spot for a patient
- **Duration**: Weeks to months until successful placement
- **Success**: Patient agrees to therapist after 1-2 initial sessions
- **Contains**: Patient data, preferences, search history, rejection tracking

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

**Data captured**:
- Demographics (including age)
- Diagnosis details
- Insurance information
- Previous therapy history
- Availability matrix (e.g., Mon 9-13, Tue 14-18, etc.)
- Preferences (therapist gender, group therapy openness)
- Exclusions (specific therapists to avoid)

### 2. Therapist Profiling

**Information gathering** (via phone/personal contact):
- Accepted diagnoses
- Age preferences
- Gender preferences
- Group vs. individual therapy preference
- Working hours (detailed weekly schedule)
- Geographic coverage
- Special requirements

**Continuous updates**:
- Preferences learned from acceptance/rejection patterns
- Schedule changes tracked over time
- "Potentially available" status maintained

### 3. Bundle Creation (Per Therapist)

**NOT regional accumulation, but therapist-specific bundling**:

Example scenario with 20 patients needing spots:
- **Therapist A** (prefers group therapy, 10km radius):
  - Bundle: 5 patients, all open for group therapy, all within 10km
- **Therapist B** (only female patients, any diagnosis):
  - Bundle: 6 patients (3 from Therapist A's bundle + 3 new), all female

**Bundle composition factors**:
1. Therapist's stated preferences (primary)
2. Geographic proximity
3. Availability compatibility
4. Diagnosis match
5. Patient wait time (fairness)

### 4. Contact Management

**Initial contact**:
- Email with bundled patient summaries
- Clear, structured format
- All pre-qualification confirmed

**Follow-up** (if no response after 7 days):
- Phone call scheduled
- Same bundle discussed
- Outcome documented

**Contact frequency limit**:
- Maximum 1 contact per therapist per month (across all patients)
- Tracked globally in system

### 5. Response Processing

**Response types**:
1. **Acceptance** (most common: 1-2 patients from bundle):
   - Schedule initial sessions
   - Track which specific patients accepted
   - Other patients return to pool
   
2. **Rejection** (all patients):
   - Document reason if given
   - Track rejection per patient-therapist pair
   - Patients return to pool for next bundle

3. **Partial acceptance**:
   - Process accepted patients
   - Return others to pool with rejection noted

4. **No response**:
   - Trigger phone follow-up after 7 days

### 6. Manual Interventions

**"Changed mind" scenario**:
- Therapist rejects bundle but later calls with sudden opening
- Staff manually selects appropriate patient
- Assignment made outside normal bundle process
- System tracks these manual placements

**Schedule updates**:
- Both patient and therapist schedules can be updated
- Changes trigger re-evaluation of compatibility

### 7. Success Tracking

**Placement success defined as**:
- Patient attends initial 1-2 sessions
- Patient agrees to continue with therapist
- Formal therapy begins

**If patient doesn't agree**:
- Search continues
- Previous therapist marked as "tried"
- New bundles created excluding this therapist

## Data Model Requirements

### Patient Search (Platzsuche)
```
- id
- patient_id (FK)
- status: active|in_sessions|successful|abandoned
- created_at
- success_date
- total_inquiries_sent
- total_therapists_contacted
- rejection_count
- manual_placement: boolean
- current_availability_schedule: JSON
```

### Therapist Inquiry (Therapeutenanfrage)
```
- id
- therapist_id (FK)
- sent_date
- sent_method: email|phone
- response_date
- response_type: accepted|rejected|no_response|partial
- included_patients: [patient_id, ...]
- accepted_patients: [patient_id, ...]
- rejected_patients: [patient_id, ...]
- staff_notes
```

### Patient-Therapist Rejection Tracking
```
- patient_id (FK)
- therapist_id (FK)
- rejection_date
- rejection_reason
- bundle_id (FK to Therapist Inquiry)
```

### Therapist Preferences
```
- therapist_id (FK)
- accepted_diagnoses: [ICD-10 codes]
- age_min
- age_max
- gender_preference: male|female|any
- group_therapy_preference: boolean
- working_hours: JSON schedule
- last_updated
- notes
```

### Patient Availability
```
- patient_id (FK)
- monday: [time_slots]
- tuesday: [time_slots]
- ...
- sunday: [time_slots]
- last_updated
- total_hours_per_week
```

## Operational Parameters

### Configurable Settings
- **Bundle size**: 3-6 patients (per therapist preference)
- **Response wait time**: 7 days before phone follow-up
- **Contact frequency**: 30 days minimum between contacts
- **Minimum availability**: 20 hours/week for patients
- **Success measurement**: After 2 initial sessions

### Manual Override Capabilities
- Emergency placement for urgent cases
- Direct assignment when therapist calls with opening
- Bundle size exceptions
- Contact frequency exceptions (documented)

## Implementation Priorities

### Phase 1: Core Refinements
1. **Detailed availability tracking**:
   - Hourly schedules for patients and therapists
   - Compatibility matching algorithm
   
2. **Therapist preference management**:
   - Structured preference storage
   - Learning from acceptance patterns
   
3. **Individual rejection tracking**:
   - Track patient-therapist rejection pairs
   - Prevent re-sending rejected patients

4. **Manual placement workflow**:
   - UI for "changed mind" scenarios
   - Audit trail for manual assignments

### Phase 2: Optimization
1. **Smart bundling algorithm**:
   - Optimize bundle composition for acceptance
   - A/B testing different strategies
   
2. **Availability matching**:
   - Automatic compatibility scoring
   - Visual schedule overlap display

3. **Success prediction**:
   - ML model for acceptance likelihood
   - Optimal bundle size per therapist

### Phase 3: Advanced Features
1. **Group therapy formation**:
   - Identify potential groups from patient pool
   - Propose complete groups to therapists
   
2. **Dynamic scheduling**:
   - Real-time availability updates
   - Automated rescheduling suggestions

## Key Business Metrics

### Success Metrics
- **Placement speed**: Days from registration to successful placement
- **Therapist acceptance rate**: % of patients accepted from bundles
- **Patient show rate**: % attending initial sessions
- **Therapist retention**: % preferring Curavani over direct inquiries

### Operational Metrics
- **Bundle efficiency**: Average accepts per bundle
- **Response rate**: % of therapists responding within 7 days
- **Manual intervention rate**: % of placements requiring manual work

## Competitive Advantage

Curavani succeeds by solving both sides' core problems:

**For Therapists**:
- Zero effort patient acquisition
- Pre-qualified, insurance-ready patients
- Preference-matched bundles
- No time wasted on unmotivated patients

**For Patients**:
- Faster placement through pooled demand
- Higher acceptance rates (pre-matching)
- Professional advocacy and follow-up

This creates a virtuous cycle where therapists prefer Curavani patients, leading to more available spots and faster placements.
