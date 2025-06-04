# Therapy Matching Platform - Business Process Documentation

## Executive Summary

This document outlines the business processes for the Psychotherapy Matching Platform, clarifying the gap between current implementation and actual business needs. The platform will support two distinct workflows: manual therapist outreach (current) and therapist self-service (future).

## Current Implementation Status

### What Exists
- ✅ Microservice architecture with Patient, Therapist, Matching, Communication, and Geocoding services
- ✅ Basic matching algorithm that filters by distance, gender preference, and exclusions
- ✅ Email batching system (groups up to 5 patients per email)
- ✅ Automatic phone call scheduling (7 days after unanswered emails)
- ✅ Contact frequency limits (1 email/week, 4-week cooldown after rejection)
- ✅ `potentially_available` field on therapists (but not used in sorting)
- ✅ Daily scraping from 116117.de for therapist data

### Key Gaps
- ❌ No API endpoint to get filtered/sorted therapist list for manual selection
- ❌ No bulk placement request creation
- ❌ Matching algorithm doesn't sort by `potentially_available` status
- ❌ No batch/campaign tracking for outreach rounds
- ❌ PlacementRequestStatus doesn't align with actual workflow
- ❌ No visibility into workload (active emails, pending calls)

## Process 1: Manual Therapy Spot Search (Current Focus)

### 1.1 Find Suitable Therapists

**What Should Happen:**
1. System filters ALL therapists based on:
   - Distance from patient (using patient's `verkehrsmittel` - car or public transit)
   - Gender preference (`bevorzugtes_therapeutengeschlecht`)
   - Patient's exclusion list (`ausgeschlossene_therapeuten`)
   - Therapist active status (not blocked/inactive)

2. System sorts results by:
   - **First**: `potentially_available = true` (therapists more likely to have spots)
   - **Then**: Distance (closest first)

**Current Reality:**
- Algorithm exists but lacks proper API endpoint
- Doesn't sort by `potentially_available`
- Returns all matches at once (no pagination/filtering)

### 1.2 Manual Therapist Selection

**What Should Happen:**
1. Staff reviews sorted list (potentially 100+ therapists)
2. Manually selects subset (e.g., 25) for first contact round
3. System creates placement requests for selected therapists
4. Tracks which "round" of outreach this is

**Current Reality:**
- Must create placement requests one by one
- No concept of outreach "rounds" or "campaigns"
- No way to track which therapists haven't been contacted yet

### 1.3 Batch Communication

**Existing Process (Works Well):**
1. Daily batch job (1 AM) groups placement requests by therapist
2. Creates emails with up to 5 patients per email
3. Respects 7-day contact frequency limit
4. Sends emails throughout the day
5. After 7 days without response, schedules phone call

**Enhancement Needed:**
- Dashboard showing current workload (pending emails, scheduled calls)
- Better tracking of which outreach round each contact belongs to

### 1.4 Response Handling

**Current Process:**
1. Email responses manually entered into system
2. Phone calls made at scheduled times, outcomes recorded
3. Placement request status updated:
   - `angenommen` (accepted) → Schedule patient-therapist meeting
   - `abgelehnt` (rejected) → 4-week cooldown period

### 1.5 Patient-Therapist Meeting

**Not Currently in System:**
- Patient and therapist meet in person
- Determine if they can work together
- Outcome: either successful match or need to continue search

### 1.6 Next Round Selection

**What Should Happen:**
1. After handling responses from first round
2. Return to filtered therapist list
3. Select next batch (e.g., 35 more)
4. Repeat process

**Current Reality:**
- No way to track who's been contacted
- Must manually track outside the system

## Process 2: Therapist Self-Service Portal (Future)

### 2.1 Therapist Groups

**Group A: Manual Contact (Current)**
- Continue existing email/phone process
- No direct system access
- All communication through staff

**Group B: Portal Access (Future)**
- Direct login to therapist portal
- Can view anonymized patient profiles
- Can offer spots or decline patients
- Reduces manual workload significantly

### 2.2 Portal Workflow (Conceptual)

1. **Therapist Login**
   - Secure authentication
   - Dashboard showing matched patients

2. **Patient Viewing**
   - See relevant patient information (anonymized)
   - Filter by their own criteria
   - Sort by match quality

3. **Spot Offering**
   - "Offer Spot" button → Notifies patient
   - "Not Suitable" button → Patient removed from their list
   - Include availability times for initial meeting

4. **Direct Communication**
   - Initial contact through platform
   - Schedule first meeting
   - Exchange necessary information

## Data Model Clarifications

### Current PlacementRequestStatus
```
OPEN: "offen"                    // Initial creation
IN_PROGRESS: "in_bearbeitung"    // Being processed
REJECTED: "abgelehnt"            // Therapist declined
ACCEPTED: "angenommen"           // Therapist accepted
```

### What's Actually Needed

**Therapist Contact Status** (per patient):
- `not_selected` - Available for selection
- `selected` - Selected for outreach but not contacted
- `email_sent` - Email sent, awaiting response
- `phone_scheduled` - No email response, call scheduled
- `responded` - Therapist has responded
- `in_cooldown` - In 4-week waiting period
- `meeting_scheduled` - Patient-therapist meeting planned
- `matched` - Successful placement
- `excluded` - Therapist excluded by patient

**Outreach Campaign Tracking**:
- Campaign/Round ID
- Date created
- Number of therapists selected
- Response rate
- Status (active/completed)

## Implementation Priorities

### Phase 1: Fix Current Workflow (Immediate)
1. **Add Therapist List Endpoint**
   ```
   GET /api/patients/{id}/available-therapists
   Response: Filtered, sorted list with contact status
   ```

2. **Add Bulk Contact Endpoint**
   ```
   POST /api/patients/{id}/contact-therapists
   Body: { therapist_ids: [...], round_name: "..." }
   ```

3. **Update Matching Algorithm**
   - Sort by `potentially_available` first
   - Include contact history in response

4. **Add Workload Dashboard Data**
   ```
   GET /api/communication/workload
   Response: { pending_emails: X, scheduled_calls: Y, awaiting_responses: Z }
   ```

### Phase 2: Enhanced Tracking (Next Sprint)
1. Campaign/round management
2. Better status tracking per therapist
3. Response rate analytics
4. Meeting outcome tracking

### Phase 3: Therapist Portal (Future)
1. Authentication system
2. Therapist dashboard
3. Patient profile viewing (anonymized)
4. Spot offering workflow
5. Communication features

## Technical Recommendations

### API Changes Needed
1. Expose existing matching algorithm via REST endpoint
2. Add bulk operations for placement requests
3. Include contact history in therapist data
4. Add campaign/round concept to data model

### Database Changes Needed
1. Add `outreach_campaigns` table
2. Add `therapist_contact_status` view/table
3. Track meeting outcomes
4. Add portal access flags to therapist model

### Business Logic Changes
1. Modify matching algorithm to sort by `potentially_available`
2. Add pagination to therapist results
3. Track which round each placement request belongs to
4. Calculate workload metrics

## Questions for Tomorrow's Discussion

1. **Potentially Available Sources**: What are the "different sources" that indicate a therapist might have availability?

2. **Meeting Outcomes**: Should the system track patient-therapist meetings and their outcomes?

3. **Workload Limits**: What's the maximum number of active emails/calls staff can handle at once?

4. **Portal Timing**: When should we start planning for the therapist portal?

5. **Selection Criteria**: Beyond `potentially_available` and distance, what factors do staff consider when manually selecting therapists?

6. **Response Time**: Besides the 7-day email-to-phone rule, are there other time-based business rules?

7. **Exclusion Management**: Can patients add to their exclusion list after failed meetings?

## Appendix: Current API Endpoints

### Relevant Existing Endpoints
- `GET /api/therapists` - List all therapists (with pagination)
- `GET /api/patients/{id}` - Get patient details including preferences
- `POST /api/placement-requests` - Create single placement request
- `GET /api/placement-requests?patient_id=X` - Get requests for a patient

### Missing Endpoints
- `GET /api/patients/{id}/available-therapists` - Get filtered/sorted therapists
- `POST /api/placement-requests/bulk` - Create multiple requests
- `GET /api/outreach-campaigns` - Track contact rounds
- `GET /api/communication/workload` - Monitor active workload

## Conclusion

The current implementation has solid technical foundations but doesn't match the actual business workflow. The system treats placement requests as individual transactions, while the business needs batch selection and campaign-based outreach. Fixing this mismatch should be the immediate priority before building the future therapist portal.