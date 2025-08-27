# Future Enhancements - Priority Items

**Document Version:** 5.3  
**Date:** January 2025  
**Status:** Requirements Gathering (Updated - 3 items completed, 1 critical bug discovered, 1 low priority item added)

---

## Implementation Priority

| Priority | Enhancement | Complexity | Impact |
|----------|-------------|------------|--------|
| **CRITICAL** | Fix Distance Constraint Bypass Bug (#30) | Medium | Critical |
| **CRITICAL** | Backup and Restore Testing & Monitoring (#24) | Medium-High | Critical |
| **CRITICAL** | Handle Duplicate Patient Registrations (#12) | Medium-High | Critical |
| **CRITICAL** | PostgreSQL Database Stability (#4) | High | Critical |
| **CRITICAL** | Protection from Injection Attacks (#21) | High | Critical |
| **CRITICAL** | Patient Excluded Therapists Removal Bug (#25) | Medium | Critical |
| **High** | Cancel Scheduled Phone Calls on Rejection (#27) | Medium | High |
| **High** | Handle "Null" Last Name in Imports (#23) | Medium | High |
| **High** | Comprehensive Email Automation System (#1) | High | Very High |
| **High** | Fix ICD10 Diagnostic Matching Logic (#18) | Medium-High | High |
| **High** | Fix Therapeutenanfrage Frontend Exit Issue (#7) | Low | High |
| **High** | Automatic Removal of Successful Platzsuchen (#5) | Medium | High |
| **High** | Patient Payment Tracking System (#16) | Medium-High | High |
| **High** | Temporarily Pause Vermittlung/Platzsuche (#19) | Medium | High |
| **High** | Validate Last Psychotherapy Date (#20) | Low-Medium | High |
| **High** | Production Container Log Management (#22) | Medium | High |
| **High** | Replace SendGrid with European Provider (#28) | Medium-High | High |
| **Medium** | Enhanced Support for Multi-Location Practices (#13) | High | Medium |
| **Medium** | Grammar Correction for Singular Patient (#14) | Low | Medium |
| **Medium** | Phone Call Templates (#15) | Medium | Medium |
| **Medium** | Track Incoming Emails (#9) | High | Medium |
| **Medium** | Add Pagination for Therapist Selection (#10) | Medium | Medium |
| **Medium** | GCS Deletion Logic (#2) | Medium | Medium |
| **Medium** | Therapist Import Reporting Fix (#3) | Low-Medium | Medium |
| **Medium** | Replace Google Cloud Storage (#21) | High | Medium |
| **Medium** | Proton Drive Backup Alternative (#29) | Low-Medium | Medium |
| **Medium** | Fix Area Code Formatting (#8) | Medium | Medium |
| **Medium** | Matching Service Cleanup (#11) | High | Medium |
| **Medium** | Phone Call Templates (#17) | Medium | Medium |
| **Low** | Fix Hyphenated Name Parsing in Scraper (#31) | Low | Low |

---

## Next Steps

1. **IMMEDIATE - Critical Bug:** Fix distance constraint bypass bug (#30) that allows invalid matches when therapist city is missing
2. **IMMEDIATE - Data Protection:** Implement backup testing and monitoring (#24) to ensure data recoverability
3. **CRITICAL - Bug Fix:** Fix excluded therapists removal bug (#25) affecting patient data integrity
4. **URGENT - Import Fix:** Handle "Null" last name issue (#23) affecting therapist imports and scraper
5. **URGENT - Security:** Implement injection attack protection (#21) across all forms
6. **URGENT:** Fix non-functional automatic reminders and follow-up systems
7. **URGENT:** Implement duplicate handling for patients (#12) to ensure data integrity
8. **URGENT:** Fix ICD10 diagnostic matching logic (#18) - review Angela Fath-Volk case
9. **Infrastructure:** Set up production log management (#22)
10. **Quick Wins:** Implement frontend fixes (#7) and validation improvements (#20)
11. **User Experience:** Implement pause functionality (#19)
12. **Email System:** Design and implement comprehensive email automation (#1)
13. **Payment System:** Design and implement patient payment tracking (#16)
14. **Communication:** Implement phone call templates (#15) and cancellation logic (#27)
15. **Data Quality:** Design and implement multi-location support (#13)
16. **European Compliance:** Plan migration from Google Cloud Storage (#21) and SendGrid (#28) to European solutions
17. **Backup Strategy:** Evaluate Proton Drive as iCloud alternative (#29)
18. **Requirements Clarification:** Schedule discussion sessions for items #2-3 and #9
19. **Implementation Planning:** Create detailed technical specifications for high-priority items
20. **Audit Current Systems:** Review therapist import reporting logic
21. **Minor Fixes:** Clean up data quality issues like hyphenated name parsing (#31) as time permits

---

## 30. Fix Distance Constraint Bypass Bug - **CRITICAL NEW**

### Current Issue
The distance constraint in the matching algorithm is being bypassed when therapists have missing city (`ort`) data, causing incorrect patient-therapist matches. When the `build_address` function cannot construct a valid address (due to missing city), it returns `None`, and the distance check **allows the match by default** instead of rejecting it.

### Discovery Context
This bug was discovered when PLZ 52159 therapists had no city data:
- **Before fix:** Therapists with missing city matched with ALL patients regardless of distance
- **After adding city:** Only patients within proper travel distance were matched
- **Impact:** Patients 50km away were incorrectly matched with therapists they couldn't reach

### Code Analysis
```python
# The problematic code in anfrage_creator.py:

def build_address(entity: Dict[str, Any]) -> Optional[str]:
    if not city:  # If city is missing
        return None  # Returns None!

def check_distance_constraint(patient, therapist):
    if not patient_address or not therapist_address:
        return True  # ALLOWS match when address is invalid!
```

### Implementation Requirements

#### A. Fix the Distance Check Logic
- **Option 1: Reject Invalid Addresses**
  ```python
  def check_distance_constraint(patient, therapist):
      patient_address = build_address(patient)
      therapist_address = build_address(therapist)
      
      if not patient_address or not therapist_address:
          # REJECT if we cannot verify distance
          logger.warning(f"Cannot verify distance - missing address data")
          return False  # Changed from True to False
  ```

- **Option 2: Use PLZ-Only Fallback**
  ```python
  def check_distance_constraint(patient, therapist):
      # Try full address first
      patient_address = build_address(patient)
      therapist_address = build_address(therapist)
      
      if not patient_address or not therapist_address:
          # Fallback to PLZ-based distance
          patient_plz = patient.get('plz')
          therapist_plz = therapist.get('plz')
          
          if patient_plz and therapist_plz:
              return check_plz_distance(patient_plz, therapist_plz, max_distance)
          
          # If still cannot calculate, reject
          return False
  ```

#### B. Data Quality Audit
- **Identify Affected Therapists:**
  ```sql
  -- Find all therapists with missing city data
  SELECT id, vorname, nachname, plz, strasse
  FROM therapist_service.therapeuten
  WHERE ort IS NULL OR ort = ''
  ORDER BY plz;
  ```

- **Review Historical Matches:**
  ```sql
  -- Find anfragen that may have incorrect matches
  SELECT DISTINCT ta.id, ta.therapist_id, t.plz, t.ort
  FROM matching_service.therapeutenanfrage ta
  JOIN therapist_service.therapeuten t ON t.id = ta.therapist_id
  WHERE t.ort IS NULL OR t.ort = ''
  AND ta.gesendet_datum IS NOT NULL;
  ```

#### C. Preventive Measures
- **Add Data Validation:**
  - Require city field for all therapist imports
  - Warn during import if city is missing
  - Add database constraint (after cleanup)

- **Monitoring:**
  - Alert when therapists have incomplete address data
  - Regular audit of address completeness
  - Track distance calculation failures

### Testing Requirements
- **Unit Tests:**
  ```python
  def test_distance_check_with_missing_city():
      patient = {'plz': '52074', 'ort': 'Aachen'}
      therapist = {'plz': '52159', 'ort': ''}  # Missing city
      
      # Should REJECT the match
      assert check_distance_constraint(patient, therapist) == False
  ```

- **Integration Tests:**
  - Test with various missing address components
  - Verify PLZ fallback behavior
  - Test with real distance calculations

### Impact Analysis
- **Affected Systems:**
  - All active platzsuchen
  - Historical anfragen with incomplete therapist data
  - Future matching accuracy

- **Potential Corrections Needed:**
  - Review past matches for validity
  - Notify affected patients/therapists if needed
  - Update existing anfragen if incorrect

### Success Metrics
- Zero matches with uncalculable distances
- 100% of therapists have complete address data
- Improved matching accuracy
- Reduced patient complaints about distance

### Priority Justification
**CRITICAL** - This bug fundamentally breaks the matching algorithm's core constraint, potentially sending patients to unreachable therapists and wasting resources on invalid matches.

---

## 1. Comprehensive Email Automation and Template System - **HIGH PRIORITY**

### Overview
Implement a comprehensive email automation system that handles all patient and therapist communications throughout the entire journey, with both automatic triggers and manual template options.

### Automatic Email Categories

#### A. Patient Onboarding & Registration
- **Welcome Email After Registration**
  - Trigger: Immediately after patient signs up
  - Content: Welcome message, next steps, required documents
  - Includes: PTV11 form requirements, timeline expectations

- **Post-Contact Signing Next Steps**
  - Trigger: After patient signs initial contact/agreement
  - Content: Clear next steps, timeline, what to expect
  - Includes: Document checklist, contact information

- **Patient Import Notifications** (to staff)
  - Trigger: Each successful GCS import
  - Recipient: `info@curavani.com`
  - Content: Patient name, import timestamp, file source, validation status

#### B. Document & Form Reminders
- **PTV11 Form Reminders**
  - Schedule: 3, 7, 14, and 21 days after registration
  - Stop after: Form submission or 4 attempts
  - Content: Importance of form, submission instructions, deadline
  - Manual option: One-click reminder button in admin

#### C. Therapy Matching Communications
- **Weekly Status Updates**
  - Trigger: Weekly for patients with active platzsuchen
  - Content: Search progress, therapists contacted, next steps
  - Opt-out option available

- **First Meeting Coordination (Without Fixed Time)**
  - Trigger: When therapist shows interest but hasn't proposed time
  - Content: Therapist contact info, suggested time ranges
  - Action: Patient to contact therapist directly

- **First Meeting Confirmation (With Proposed Time)**
  - Trigger: When therapist suggests specific appointment time
  - Content: Proposed time, location, confirmation request
  - Actions: Accept/decline buttons, alternative time request

- **Patient-Initiated Therapist Contact Templates** (**UPDATED**)
  - Trigger: When patient needs to contact therapist for Erstgespräch
  - Content: Pre-written email templates for patients to use
  - Templates include:
    - Initial contact request for appointment
    - Response to therapist's availability
    - Rescheduling request
    - Confirmation of appointment
  - Delivery: Send templates to patient with clear instructions
  - Format: Copy-paste ready text with placeholder fields

- **Therapist Rejection Follow-up**
  - Trigger: When therapist rejects patient (no availability, etc.)
  - Content: Acknowledgment, alternative options, continued search
  - Tone: Supportive and encouraging

#### D. Ongoing Care & Follow-up
- **Therapy Check-in Emails**
  - Schedule: 4 weeks after therapy start, then quarterly
  - Content: Satisfaction check, support offer, feedback request
  - Purpose: Ensure therapy is progressing well

### Manual Email Templates

#### Categories of Templates
1. **Initial Contact Templates**
   - First outreach to patients
   - Information requests
   - Document reminders
   - **Patient email templates for therapist contact** (new)

2. **Status Update Templates**
   - Search progress updates
   - Waiting list notifications
   - General check-ins

3. **Problem Resolution Templates**
   - Payment issues
   - Document problems
   - Complaint responses

4. **Appointment Coordination**
   - Schedule changes
   - Cancellations
   - Rescheduling
   - **Templates for patients to contact therapists** (new)

### Implementation Details

#### Technical Architecture
- **Email Service Enhancement**
  - Centralized template management system
  - Variable substitution engine
  - Multi-language support (German primary)
  - HTML and plain text versions

- **Automation Engine**
  - Event-driven triggers
  - Scheduled job processor
  - Rate limiting and throttling
  - Retry logic for failures

- **Template Management System**
  - WYSIWYG editor for staff
  - Version control for templates
  - A/B testing capability
  - Preview functionality

#### Database Schema
```sql
email_templates (
  id, name, category, subject, body_html, body_text,
  variables, trigger_type, schedule, version, active
)

email_automation_rules (
  id, template_id, trigger_event, conditions,
  delay_minutes, max_sends, active
)

email_log (
  id, patient_id, template_id, sent_at, status,
  open_count, click_count, error_message
)
```

#### Configuration Options
- Enable/disable individual automation rules
- Customizable sending schedules
- Business hours enforcement
- Holiday blackout dates
- Per-patient opt-out preferences

### Success Metrics
- Email open rates by category
- Response/action rates
- Reduction in manual follow-ups
- Patient satisfaction scores
- Time saved by staff

### GDPR Compliance
- Clear consent mechanisms
- Unsubscribe options in all emails
- Data retention policies
- Audit trail for all communications

---

## 2. GCS File Deletion Logic Enhancement

### Current Issue
Need to ensure GCS files are only deleted after successful import to patient-service.

### Questions for Discussion
- Currently, are files being **deleted from GCS before confirming** the import was successful in patient-service?
- What constitutes **"full import success"** - just the database write, or also validation, processing, etc.?
- Should there be **retry logic** for failed imports before giving up?
- What should happen to **files that permanently fail import** - keep forever, delete after X days, move to error bucket?

### Implementation Areas
- Modify import workflow to confirm success before deletion
- Add retry mechanism for failed imports
- Define cleanup strategy for failed import files

---

## 3. Therapist Import Reporting Corrections

### Current Issue
Reporting of therapist imports shows incorrect numbers for successful and failed imports.

### Specific Data Quality Issues to Investigate
- **Silvina Spivak de Weissmann:** Check if "Spivak" is being incorrectly parsed as middle name instead of part of last name "Spivak de Weissmann"
- **Name Parsing Logic:** Review how compound last names with "de", "von", "van" are handled
- **Import Statistics:** Verify that these parsing errors are properly reflected in import reports

### Questions for Discussion
- What **kind of therapist imports** are these (from external source, CSV uploads, API sync)?
- What specifically is wrong - **overcounting, undercounting, or wrong success/failure categorization**?
- **Where are these reports shown** (admin UI, email summaries, dashboard, logs)?
- Are the **actual imports working correctly** and it's just the reporting numbers that are wrong?
- How are compound last names being parsed and stored?

### Investigation Areas
- Audit import counting logic
- Review success/failure criteria
- Check for duplicate counting
- Validate report generation queries
- Implement import audit trail
- **Review name parsing algorithm for compound names**
- **Check specific case: Silvina Spivak de Weissmann**

---

## 4. PostgreSQL Database Stability Investigation - **HIGH PRIORITY**

### Current Issue
PostgreSQL database in production is frequently crashing, causing system downtime and data availability issues.

### Investigation Required
- **Root Cause Analysis:** Determine why the database is crashing
- **Log Analysis:** Review PostgreSQL logs for error patterns
- **Resource Monitoring:** Check memory, disk space, CPU usage
- **Query Performance:** Identify slow or problematic queries
- **Connection Analysis:** Review connection pooling and limits
- **Hardware Assessment:** Validate server capacity and performance

### Potential Causes to Investigate
- Memory exhaustion (shared_buffers, work_mem settings)
- Disk space issues (WAL files, temp files, data growth)
- Long-running or blocking queries
- Connection pool exhaustion
- Hardware failures or resource constraints
- PostgreSQL configuration issues
- Backup or maintenance operations causing locks

### Immediate Actions Needed
- Set up comprehensive database monitoring
- Implement automated alerting for database issues
- Review and optimize PostgreSQL configuration
- Establish database backup and recovery procedures
- Plan for high availability setup

---

## 5. Automatic Removal of Successful Platzsuchen from Other Therapeutenanfragen - **NEW**

### Current Issue
When a patient is successfully matched (angenommen) in one therapeutenanfrage, they remain in all other pending therapeutenanfragen. This creates confusion and potential duplicate acceptances.

### Requirement
Implement automatic cleanup: when a patient's platzsuche becomes "erfolgreich", remove them from all other therapeutenanfragen where they haven't been answered yet.

### Implementation Details
- **Trigger:** When a patient is marked as "angenommen" in any therapeutenanfrage
- **Action:** 
  - Mark the platzsuche as "erfolgreich"
  - Find all other therapeutenanfragen containing this patient
  - For those where the patient hasn't been answered yet:
    - Update patient status to indicate they were matched elsewhere
    - Update the therapeutenanfrage response counts
    - Notify therapist if the anfrage was already sent

### Technical Considerations
- Add new patient outcome status: "matched_elsewhere" or similar
- Create background job/event handler for cleanup
- Consider race conditions if multiple therapists accept simultaneously
- Add audit trail for transparency
- Update frontend to show when patients were matched elsewhere

### Backend Changes Needed
- New endpoint or enhancement to existing response recording
- Kafka event for successful match propagation
- Database queries to find and update affected records
- Email notifications for affected therapists

---

## 7. Fix Therapeutenanfrage Frontend Exit Issue - **NEW**

### Current Issue
When a therapeutenanfrage is created but contains 0 patients, the frontend provides no proper way to exit or quit the process.

### Requirement
Implement proper navigation controls for empty therapeutenanfragen.

### Implementation Details
- **Add Exit/Cancel Button:** Clear navigation option to return to previous screen
- **Empty State Handling:** Show appropriate message when no patients are present
- **Navigation Logic:** 
  - Return to patient selection screen
  - Option to add patients directly
  - Clear indication of next steps

### Frontend Changes
- Add "Cancel" or "Back" button with proper routing
- Implement empty state UI component
- Add confirmation dialog for unsaved changes
- Update breadcrumb navigation

### User Experience Improvements
- Clear visual indicators for empty state
- Helpful guidance text for next actions
- Consistent with other form cancellation patterns

---

## 8. Fix Area Code Formatting Issue - **NEW**

### Current Issue
Frontend always formats area codes as 4 digits, but some German cities have 5-digit area codes (e.g., Berlin 030 vs. smaller cities with 5 digits), causing incorrect phone number display and potential calling issues.

### Examples of German Area Codes
- **2-digit:** None in Germany
- **3-digit:** Major cities (030 Berlin, 089 Munich, 040 Hamburg)
- **4-digit:** Most common (0221 Cologne, 0711 Stuttgart)
- **5-digit:** Smaller cities and rural areas (03581 Görlitz, 04928 Schlieben)

### Implementation Requirements
- **Dynamic Area Code Detection:**
  - Implement lookup table for German area codes
  - Detect area code length based on prefix
  - Format numbers correctly based on actual area code length

- **Formatting Logic:**
  ```javascript
  function formatGermanPhoneNumber(number) {
    const cleaned = number.replace(/\D/g, '');
    
    // Detect area code length from lookup table
    const areaCodeLength = detectAreaCodeLength(cleaned);
    
    // Format based on detected length
    if (areaCodeLength === 3) {
      // e.g., 030 1234567
      return `${cleaned.slice(0, 3)} ${cleaned.slice(3)}`;
    } else if (areaCodeLength === 4) {
      // e.g., 0221 1234567
      return `${cleaned.slice(0, 4)} ${cleaned.slice(4)}`;
    } else if (areaCodeLength === 5) {
      // e.g., 03581 123456
      return `${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
    }
    
    // Fallback formatting
    return number;
  }
  ```

### Technical Implementation
- **Area Code Database:**
  - Create comprehensive list of German area codes
  - Include mobile prefixes (015x, 016x, 017x)
  - Regular updates for new area codes

- **Frontend Updates:**
  - Replace hardcoded 4-digit formatting
  - Implement dynamic formatter
  - Add unit tests for various area codes
  - Update all phone number display components

### Testing Requirements
- Test with all area code lengths (3, 4, 5 digits)
- Verify mobile number formatting
- International number handling
- Edge cases and invalid numbers

### User Experience
- Correct phone number display
- Improved readability
- Accurate copy/paste functionality
- Better user confidence in data accuracy

---

## 9. Track Incoming Emails - **NEW**

### Requirement
Implement comprehensive incoming email tracking system to monitor and integrate email communications with patient records.

### Specification
- **IMAP Connector:** Integrate IMAP functionality into communication service
- **Email Monitoring:** Track incoming emails to system email addresses
- **Patient Correlation:** Match incoming emails to patient records
- **Response Tracking:** Track replies to system-sent emails

### Implementation Details
- **IMAP Integration:**
  - Connect to email server via IMAP
  - Monitor specified inboxes (info@curavani.com, etc.)
  - Parse incoming email metadata and content
  - Handle attachments and embedded content

- **Email Processing:**
  - Extract sender information and correlate with patient records
  - Categorize email types (replies, new inquiries, form submissions)
  - Store email content and metadata in database
  - Trigger appropriate workflow actions

### Technical Considerations
- Implement secure IMAP connection with authentication
- Add email parsing and content extraction
- Create database schema for incoming email tracking
- Implement duplicate detection and deduplication
- Add email archiving and retention policies
- Consider spam filtering and security scanning

### Integration Points
- Patient management system
- Communication service
- Notification system
- Admin dashboard for email monitoring

---

## 10. Add Pagination for Therapist Selection in Vermittlung - **NEW**

### Requirement
Implement pagination for therapist selection in the vermittlung process of therapeutenanfragen to improve performance and user experience.

### Current Issue
Large therapist lists in the therapeutenanfrage form cause performance issues and poor user experience.

### Implementation Details
- **Frontend Pagination:**
  - Add pagination controls to therapist selection component
  - Implement page size options (10, 25, 50 therapists per page)
  - Add search and filtering capabilities
  - Maintain selected therapists across pages

- **Backend Optimization:**
  - Implement paginated API endpoints for therapist retrieval
  - Add efficient database queries with LIMIT/OFFSET
  - Include total count and pagination metadata
  - Optimize therapist filtering and search queries

### Technical Changes
- Update therapeutenanfrage form component
- Add pagination component library or custom implementation
- Modify therapist API endpoints
- Update state management for selected therapists
- Add search and filter functionality

### User Experience Improvements
- Faster page loading with smaller data sets
- Better navigation through large therapist lists
- Improved search and filtering capabilities
- Clear indication of total available therapists

---

## 11. Matching Service Cleanup - **NEW**

### Current Issue
The matching service requires cleanup and optimization as described in the separate matching service document.

### Requirement
Implement comprehensive cleanup of the matching service to improve performance, maintainability, and reliability.

### Implementation Areas
- **Code Refactoring:**
  - Remove duplicate code
  - Improve error handling
  - Optimize database queries
  - Standardize coding patterns

- **Performance Optimization:**
  - Implement caching strategies
  - Optimize matching algorithms
  - Reduce database round trips
  - Improve query performance

- **Architecture Improvements:**
  - Separate concerns properly
  - Implement proper service boundaries
  - Add comprehensive logging
  - Improve testability

### Technical Tasks
- **Database Optimization:**
  - Add missing indexes
  - Optimize complex queries
  - Implement query result caching
  - Review and optimize joins

- **Service Refactoring:**
  - Extract common functionality
  - Implement proper interfaces
  - Add dependency injection
  - Improve configuration management

- **Testing Enhancement:**
  - Add unit tests for all components
  - Implement integration tests
  - Add performance benchmarks
  - Create test data generators

### Documentation Requirements
- Update API documentation
- Create service architecture diagrams
- Document matching algorithms
- Add troubleshooting guide

### Success Metrics
- Reduced matching time by 50%
- Improved code coverage to 80%+
- Reduced bug reports by 40%
- Better service reliability

---

## 12. Handle Duplicate Patient Registrations During Import - **NEW**

### Current Issue
Patients can register multiple times on the website, creating duplicate records in the system. This leads to data integrity issues, inefficient resource usage, and confusion in patient management.

### Requirement
Implement robust duplicate detection and handling mechanism for patient imports and registrations.

### Implementation Details
- **Duplicate Detection Methods:**
  - Create and maintain email hash index for quick duplicate checking
  - Compare normalized email addresses (lowercase, trim whitespace)
  - Consider additional matching criteria:
    - Phone number matching
    - Name + birthdate combination
    - Address similarity scoring

- **Email Hash Implementation:**
  - Generate SHA-256 hash of normalized email addresses
  - Store hashes in indexed database column or Redis cache
  - Check against hash list before creating new patient records
  - Update hash list in real-time as patients are added

- **Duplicate Handling Strategies:**
  - **Merge Strategy:** Combine data from duplicate registrations
  - **Update Strategy:** Update existing record with new information
  - **Reject Strategy:** Reject duplicate and notify user
  - **Manual Review:** Flag for admin review

### Technical Considerations
- Create database index on email hash for performance
- Implement batch duplicate checking for bulk imports
- Add duplicate detection to both import process and web registration
- Create audit trail for merged/updated records
- Handle edge cases (email changes, typos, etc.)

### User Experience
- Clear messaging when duplicate registration attempted
- Option to update existing information
- Admin interface to review and resolve duplicates
- Duplicate statistics and reporting

### GDPR Compliance
- Ensure email hashing is one-way and irreversible
- Document duplicate handling in privacy policy
- Provide transparency about data merging

---

## 13. Enhanced Support for Multi-Location Practices - **NEW**

### Current Issue
Practices with two or more locations are currently treated as independent duplicates in the system, causing confusion and inefficient management of therapist data.

### Requirement
Implement proper support for practices with multiple locations while maintaining distinct location information.

### Implementation Details
- **Data Model Enhancement:**
  - Create `practice` entity to group related locations
  - Add `location` entity linked to practices
  - Allow therapists to be associated with multiple locations
  - Track primary vs secondary locations for therapists

- **Location Management:**
  - Each location maintains separate:
    - Address and contact information
    - Operating hours
    - Available services
    - Capacity information
  - Shared across locations:
    - Practice name and branding
    - Administrative contacts
    - Billing information

- **Search and Matching:**
  - Include all practice locations in therapist searches
  - Show distance to each location
  - Allow patients to select preferred location
  - Consider availability at each location separately

### Technical Implementation
- **Database Schema:**
  ```sql
  practices (id, name, primary_email, website)
  practice_locations (id, practice_id, address, city, postal_code, phone)
  therapist_locations (therapist_id, location_id, is_primary, days_available)
  ```

- **API Changes:**
  - New endpoints for practice management
  - Updated therapist endpoints to include location data
  - Location-aware search functionality

- **Import Process:**
  - Detect practices based on shared attributes
  - Group locations automatically where possible
  - Manual review interface for ambiguous cases

### Benefits
- Accurate representation of practice structures
- Better patient-therapist matching
- Reduced duplicate data entry
- Improved location-based searching

---

## 14. Grammar Correction for Singular Patient in Therapeutenanfrage - **NEW**

### Current Issue
When a therapeutenanfrage contains only 1 patient, the system uses plural grammar forms, creating unprofessional communications.

### Requirement
Implement dynamic text adjustment to use singular forms when exactly one patient is in a therapeutenanfrage.

### Implementation Details
- **Text Templates to Update:**
  - Email subjects and bodies
  - UI labels and messages
  - PDF reports and documents
  - Notification messages

- **Conditional Logic:**
  ```javascript
  // Example implementation
  const patientText = patientCount === 1 
    ? "1 Patient" 
    : `${patientCount} Patienten`;
  
  const verbForm = patientCount === 1 
    ? "wurde" 
    : "wurden";
  ```

- **Affected Areas:**
  - Therapeutenanfrage creation confirmation
  - Email templates to therapists
  - Dashboard statistics
  - Report generation
  - Status messages

### Technical Implementation
- Create localization helper functions
- Update all email templates
- Modify frontend components
- Add pluralization logic to backend
- Test all edge cases (0, 1, many)

### Languages to Support
- German (primary)
- Consider English translations

---

## 15. Phone Call Templates for Patient Communication - **NEW**

### Current Issue
Staff members lack standardized scripts for phone calls with patients, leading to inconsistent communication and missed important topics.

### Requirement
Create customizable phone call templates for various patient interaction scenarios.

### Template Categories
- **First Contact Call:**
  - Introduction and verification
  - Explanation of services
  - Initial information gathering
  - Next steps explanation

- **Follow-up Calls:**
  - Status updates
  - Document reminders
  - Appointment scheduling
  - Problem resolution

- **Special Situations:**
  - Payment discussions
  - Complaint handling
  - Emergency protocols
  - Therapist matching updates

### Implementation Details
- **Template Management System:**
  - Create/edit/delete templates
  - Version control for templates
  - Categorization and tagging
  - Search functionality

- **Call Script Features:**
  - Dynamic field insertion (patient name, dates, etc.)
  - Branching logic for different scenarios
  - Checkboxes for covered topics
  - Notes section for call outcomes

- **Integration Points:**
  - Link templates to patient records
  - Auto-populate patient information
  - Save call notes to patient history
  - Generate follow-up tasks

### Technical Implementation
- Database schema for templates
- Template editor interface
- Variable substitution engine
- Call history tracking
- Reporting on template usage

### Training and Compliance
- Mandatory templates for certain call types
- Training mode for new staff
- Quality assurance reviews
- Performance metrics

---

## 16. Patient Payment Tracking System - **NEW**

### Current Issue
No systematic way to document whether patients have paid for services, causing billing confusion and follow-up difficulties.

### Requirement
Implement comprehensive payment tracking functionality integrated with patient records. Furthermore, implement that patients get an email after the payment is confirmed. So they know that the search is starting now for them.

### Payment Information to Track
- **Payment Status:**
  - Not yet billed
  - Invoice sent
  - Partially paid
  - Fully paid
  - Overdue
  - Disputed

- **Payment Details:**
  - Invoice number and date
  - Amount due and paid
  - Payment method
  - Payment date
  - Outstanding balance

- **Payment Types:**
  - Registration fees
  - Service charges
  - Additional assessments
  - Refunds/credits

### Implementation Details
- **Database Schema:**
  ```sql
  patient_payments (
    id, patient_id, invoice_number,
    amount_due, amount_paid, 
    payment_date, payment_method,
    status, notes
  )
  ```

- **User Interface:**
  - Payment status indicator on patient profile
  - Payment history tab
  - Quick payment entry form
  - Bulk payment processing
  - Payment reports and exports

- **Automated Features:**
  - Overdue payment alerts
  - Payment reminder emails
  - Receipt generation
  - Monthly billing reports
  - **Payment confirmation email to patient**

### Integration Points
- Patient management system
- Email communication service
- Accounting software export
- Dashboard statistics

### Compliance Considerations
- GDPR compliance for financial data
- Audit trail for all payment changes
- Access control for payment information
- Data retention policies

---

## 17. Phone Call Templates - **NEW**

### Current Issue
Staff members lack standardized scripts for phone calls with patients, leading to inconsistent communication and missed important topics.

### Requirement
Create customizable phone call templates for various patient interaction scenarios.

### Template Categories
- **First Contact Call:**
  - Introduction and verification
  - Explanation of services
  - Initial information gathering
  - Next steps explanation

- **Follow-up Calls:**
  - Status updates
  - Document reminders
  - Appointment scheduling
  - Problem resolution

- **Special Situations:**
  - Payment discussions
  - Complaint handling
  - Emergency protocols
  - Therapist matching updates

### Implementation Details
- **Template Management System:**
  - Create/edit/delete templates
  - Version control for templates
  - Categorization and tagging
  - Search functionality

- **Call Script Features:**
  - Dynamic field insertion (patient name, dates, etc.)
  - Branching logic for different scenarios
  - Checkboxes for covered topics
  - Notes section for call outcomes

- **Integration Points:**
  - Link templates to patient records
  - Auto-populate patient information
  - Save call notes to patient history
  - Generate follow-up tasks

### Technical Implementation
- Database schema for templates
- Template editor interface
- Variable substitution engine
- Call history tracking
- Reporting on template usage

### Training and Compliance
- Mandatory templates for certain call types
- Training mode for new staff
- Quality assurance reviews
- Performance metrics

---

## 18. Fix ICD10 Diagnostic Matching Logic - **HIGH PRIORITY NEW**

### Current Issue
The logic for matching patient ICD10 diagnoses with therapist preferences needs to be reviewed and fixed. Specifically, single/parent diagnoses from patients are not properly matching with therapist group preferences (subcategories).

### Example Case
- **Therapist:** Angela Fath-Volk
- **Issue:** Patient with single diagnosis F40 or F41 not matching with therapist who has preferences for F40.0, F40.1, etc.
- **Expected Behavior:** Parent diagnosis (F40) should match all child diagnoses (F40.0, F40.1, F40.2, etc.)

### Requirements
Implement proper hierarchical matching logic for ICD10 codes where:
- Parent codes (e.g., F40, F41) match all their subcategories
- Exact matches still take precedence
- Bidirectional matching works correctly

### Implementation Details
- **Matching Logic Enhancement:**
  - Patient diagnosis F40 should match therapist preferences: F40, F40.0, F40.1, F40.2, etc.
  - Patient diagnosis F40.1 should match therapist preferences: F40, F40.1
  - Consider ICD10 hierarchy depth (up to 5 levels)

- **Database Queries:**
  - Update matching queries to use LIKE operator for prefix matching
  - Consider creating ICD10 hierarchy lookup table
  - Optimize for performance with proper indexes

- **Test Cases:**
  ```
  Patient: F40    → Therapist: F40.0  ✓ (should match)
  Patient: F40    → Therapist: F41.0  ✗ (should not match)
  Patient: F40.1  → Therapist: F40    ✓ (should match)
  Patient: F40.1  → Therapist: F40.1  ✓ (should match)
  Patient: F40.1  → Therapist: F40.2  ✗ (should not match)
  ```

### Technical Implementation
- **Algorithm Update:**
  ```sql
  -- Example matching logic
  SELECT * FROM therapists t
  WHERE EXISTS (
    SELECT 1 FROM therapist_icd10_preferences p
    WHERE p.therapist_id = t.id
    AND (
      p.icd10_code = patient_diagnosis -- exact match
      OR patient_diagnosis LIKE p.icd10_code || '%' -- patient has parent
      OR p.icd10_code LIKE patient_diagnosis || '%' -- therapist has parent
    )
  )
  ```

- **Performance Optimization:**
  - Create ICD10 hierarchy table with parent-child relationships
  - Use materialized views for common matching patterns
  - Add appropriate database indexes

### Investigation Areas
- Audit current matching algorithm
- Review all edge cases in production
- Check Angela Fath-Volk specific configuration
- Identify other affected therapist-patient pairs
- Performance impact of enhanced matching

### Testing Requirements
- Comprehensive unit tests for all matching scenarios
- Integration tests with real ICD10 codes
- Performance testing with large datasets
- Manual verification of known problematic cases

---

## 19. Temporarily Pause Vermittlung/Platzsuche for Patient Holidays - **NEW**

### Current Issue
When patients go on holiday or are temporarily unavailable, there's no way to pause their vermittlung/platzsuche activities, leading to wasted efforts contacting therapists on their behalf.

### Requirement
Implement functionality to temporarily pause and resume platzsuche activities with clear date ranges and automatic reactivation.

### Implementation Details
- **Pause Features:**
  - Set start and end dates for pause period
  - Automatic reactivation after end date
  - Manual reactivation option
  - Pause reason documentation (holiday, medical, other)

- **System Behavior During Pause:**
  - Exclude patient from new therapeutenanfragen
  - Pause automatic reminders and follow-ups
  - Show pause status in patient overview
  - Notify therapists if already in active anfragen

- **UI Components:**
  - Pause button on platzsuche details
  - Date picker for pause period
  - Status indicator showing pause state
  - Countdown to automatic reactivation

### Technical Implementation
- **Database Changes:**
  ```sql
  platzsuche_pauses (
    id, platzsuche_id, 
    pause_start, pause_end,
    pause_reason, 
    created_by, created_at
  )
  ```

- **Backend Logic:**
  - Scheduled job to check for pause expirations
  - Exclude paused patients from matching queries
  - API endpoints for pause management
  - Event notifications for pause state changes

- **Frontend Updates:**
  - Pause management interface
  - Visual indicators in patient lists
  - Dashboard statistics excluding paused patients
  - Pause history in patient timeline

### Business Rules
- Maximum pause duration (e.g., 3 months)
- Minimum pause duration (e.g., 1 week)
- Notification before automatic reactivation
- Audit trail for all pause actions

---

## 20. Validate Last Psychotherapy Date in Registration Process - **NEW**

### Current Issue
Invalid or implausible dates for last psychotherapy are being entered during patient registration, causing data quality issues and affecting eligibility assessments.

### Requirement
Implement comprehensive validation for the "date of last psychotherapy" field during the registration process.

### Validation Rules
- **Date Range Validation:**
  - Cannot be in the future
  - Cannot be before patient's birth date
  - Reasonable historical limit (e.g., not more than 50 years ago)
  - Warning for very recent dates (might indicate ongoing therapy)

- **Business Logic Validation:**
  - Check against patient age (therapy date when patient was adult/child)
  - Flag suspicious patterns (e.g., exactly 1 year ago)
  - Validate format consistency (DD.MM.YYYY)

- **User Experience:**
  - Real-time validation feedback
  - Clear error messages explaining why date is invalid
  - Suggestions for common mistakes (wrong year, day/month swap)
  - Optional field with clear indication

### Technical Implementation
- **Frontend Validation:**
  ```javascript
  // Example validation logic
  validateLastTherapyDate(date, birthDate) {
    const today = new Date();
    const therapyDate = new Date(date);
    const birth = new Date(birthDate);
    
    if (therapyDate > today) {
      return "Date cannot be in the future";
    }
    if (therapyDate < birth) {
      return "Therapy date cannot be before birth date";
    }
    // Additional validations...
  }
  ```

- **Backend Validation:**
  - Double-check all frontend validations
  - Store validation warnings for review
  - Flag questionable entries for manual verification
  - Generate data quality reports

### Integration Points
- Registration form validation
- Import process validation
- Data migration cleanup scripts
- Admin interface for reviewing flagged entries

---

## 21. Replace Google Cloud Storage with European Solution - **NEW**

### Current Issue
Google Cloud Storage may not meet European data sovereignty requirements and could be unnecessarily complex for the application's needs.

### Requirement
Replace GCS with a simpler, GDPR-compliant European storage solution.

### Evaluation Criteria
- **Data Sovereignty:** Must store data within EU borders
- **GDPR Compliance:** Full compliance with European privacy laws
- **Simplicity:** Easier to manage than current GCS setup
- **Cost Effectiveness:** Competitive or lower pricing
- **Reliability:** High availability and durability

### Potential Solutions
- **European Providers:**
  - OVHcloud Object Storage (France)
  - Scaleway Object Storage (France)
  - Hetzner Storage Boxes (Germany)
  - IONOS Cloud Storage (Germany)
  
- **Self-Hosted Options:**
  - MinIO on European servers
  - NextCloud storage
  - Simple NFS/SFTP servers

### Migration Plan
- **Phase 1: Evaluation**
  - Compare providers on criteria
  - Proof of concept with top candidates
  - Cost analysis
  
- **Phase 2: Implementation**
  - Set up new storage solution
  - Implement storage abstraction layer
  - Update all GCS references in code
  
- **Phase 3: Migration**
  - Parallel running period
  - Incremental data migration
  - Verification and testing
  - Cutover and GCS decommission

### Technical Considerations
- API compatibility requirements
- Backup and disaster recovery
- Access control and encryption
- Integration with existing services
- Performance requirements

---

## 21. Protection from Injection Attacks in Forms - **CRITICAL NEW**

### Current Issue
Forms throughout the application need protection against injection attacks (SQL injection, XSS, etc.) to ensure system security.

### Areas Requiring Protection
- **Email Validation Forms**
  - Registration forms on website
  - Email update forms
  - Contact forms

- **Data Import Processes**
  - Patient import from CSV/Excel
  - Therapist import mechanisms
  - Bulk data uploads

- **All User Input Forms**
  - Patient registration
  - Therapist profiles
  - Search queries
  - Free text fields

### Implementation Requirements
- **Input Validation:**
  - Whitelist allowed characters for each field type
  - Escape special characters
  - Validate data types and formats
  - Length restrictions on all inputs

- **SQL Injection Prevention:**
  - Use parameterized queries everywhere
  - Never concatenate user input into SQL
  - Implement stored procedures where appropriate
  - Regular security audits of database queries

- **XSS Prevention:**
  - HTML encode all output
  - Content Security Policy headers
  - Sanitize rich text inputs
  - Validate file uploads

### Technical Implementation
- **Backend Security:**
  ```javascript
  // Example parameterized query
  const query = 'SELECT * FROM patients WHERE email = $1';
  const values = [sanitizedEmail];
  
  // Input sanitization
  const sanitizeInput = (input) => {
    return input.replace(/[<>'"]/g, '');
  };
  ```

- **Frontend Validation:**
  - Client-side validation as first line of defense
  - Server-side validation as authoritative check
  - Use security libraries (e.g., DOMPurify)
  - Regular expression validation

### Security Measures
- Implement Web Application Firewall (WAF)
- Regular penetration testing
- Security headers configuration
- Input validation middleware
- Audit logging for suspicious activities

### Priority
**CRITICAL** - Security vulnerabilities can compromise entire system

---

## 22. Production Container Log Management - **NEW**

### Current Issue
Production logs need better management - currently showing too many INFO level logs and missing proper monitoring for WARNING level events.

### Requirements
- **Log Level Management:**
  - Remove INFO logs from production
  - Keep INFO logs in development/test environments
  - Ensure WARNING and ERROR logs are captured
  - Implement proper log rotation

- **Monitoring Setup:**
  - Alert on WARNING level logs
  - Aggregate ERROR logs for immediate attention
  - Create dashboards for log analytics
  - Set up log retention policies

### Implementation Details
- **Environment-Based Configuration:**
  ```javascript
  // Example log configuration
  const logLevel = process.env.NODE_ENV === 'production' 
    ? 'WARNING' 
    : 'INFO';
  
  logger.configure({
    level: logLevel,
    format: productionFormat,
    transports: [...]
  });
  ```

- **Monitoring Tools:**
  - Set up log aggregation (ELK, Grafana Loki, etc.)
  - Configure alerting rules
  - Create monitoring dashboards
  - Implement log analysis tools

- **Best Practices:**
  - Structured logging (JSON format)
  - Consistent log formats across services
  - Meaningful log messages
  - Proper error context
  - No sensitive data in logs

### Technical Implementation
- Update logging configuration in all services
- Implement centralized logging
- Set up monitoring and alerting
- Create runbooks for common warnings
- Regular log review process

### Benefits
- Reduced log noise in production
- Faster issue identification
- Better system observability
- Improved debugging capabilities
- Compliance with logging best practices

---

## 23. Handle "Null" Last Name in Therapist Imports and Scraper - **HIGH PRIORITY NEW**

### Current Issue
Therapists with the literal last name "Null" (e.g., Anne-Kathrin Null) are causing import failures and scraper issues. The system is interpreting the string "Null" as a null value, leading to data processing errors.

### Example Case
- **Therapist:** Anne-Kathrin Null (File: 10243.json)
- **Error:** "Failed to map therapist data"
- **Import Summary:** 8262 therapists processed, 1 failed (100% success rate affected)

### Root Causes
- **String-to-Null Conversion:** The string "Null" is being interpreted as a null/None value
- **JSON Parsing Issues:** JSON deserializers may auto-convert "Null" strings
- **Database Constraints:** NOT NULL constraints on last name field reject null values
- **Scraper Issues:** Web scraper may skip or error on "Null" values

### Implementation Requirements

#### A. Input Validation & Sanitization
- **String Preservation:**
  - Treat "Null" as a valid string, not a null value
  - Case-insensitive handling ("null", "NULL", "Null")
  - Preserve original casing in database

- **Validation Rules:**
  ```python
  def validate_last_name(value):
      # Check if value is actually None vs string "Null"
      if value is None:
          raise ValueError("Last name cannot be empty")
      
      # Ensure string "Null" is preserved
      if isinstance(value, str) and value.lower() == "null":
          # Mark for special handling
          return {"value": value, "is_literal_null": True}
      
      return {"value": value, "is_literal_null": False}
  ```

#### B. Import Process Updates
- **JSON Parsing:**
  ```python
  # Custom JSON decoder to preserve "Null" strings
  def custom_decoder(dct):
      for key, value in dct.items():
          if key in ['nachname', 'last_name'] and value == "Null":
              # Explicitly preserve as string
              dct[key] = str(value)
      return dct
  
  # Use: json.loads(data, object_hook=custom_decoder)
  ```

- **Database Handling:**
  - Add check constraint to differentiate empty string from "Null"
  - Consider adding metadata flag for literal null names
  - Update ORM mappings to handle special case

#### C. Scraper Enhancements
- **Web Scraping:**
  - Add special handling for "Null" text in name fields
  - Implement fallback logic if "Null" causes parsing errors
  - Log occurrences for monitoring

- **Data Extraction:**
  ```javascript
  // Scraper logic
  const lastName = element.textContent.trim();
  
  // Preserve "Null" as string
  if (lastName.toLowerCase() === 'null') {
      return { lastName: 'Null', hasLiteralNullName: true };
  }
  
  return { lastName: lastName || '' };
  ```

#### D. System-Wide Fixes
- **API Responses:**
  - Ensure APIs return "Null" as string, not null
  - Add response headers indicating special handling

- **Frontend Display:**
  - Show "Null" correctly in UI components
  - Add tooltip or indicator for literal null names

- **Search Functionality:**
  - Enable searching for therapists with "Null" last name
  - Case-insensitive search should find "Null" entries

### Testing Requirements
- **Unit Tests:**
  - Test import with "Null" last name
  - Test JSON parsing preservation
  - Test database insert/update/select
  - Test API serialization

- **Integration Tests:**
  - Full import cycle with "Null" name
  - Scraper handling of "Null" values
  - End-to-end data flow

- **Edge Cases:**
  - Multiple "Null" variations (NULL, null, Null)
  - Other problematic names (True, False, None, Undefined)
  - International variants (Nul, Nullo)

### Preventive Measures
- **Reserved Word List:**
  ```python
  RESERVED_WORDS = [
      'null', 'none', 'undefined', 'true', 'false',
      'nil', 'void', 'empty', 'blank'
  ]
  
  def requires_special_handling(value):
      return value.lower() in RESERVED_WORDS
  ```

- **Documentation:**
  - Document all reserved words requiring special handling
  - Create guidelines for handling edge cases
  - Add comments in code for future developers

### Monitoring & Alerts
- Set up alerts for import failures with "reserved word" names
- Track occurrences of special-case handling
- Regular audit of therapist names for data quality

### Success Metrics
- **Import Success Rate:** Return to 100% with "Null" names handled
- **Zero Data Loss:** All therapist records preserved accurately
- **Search Accuracy:** "Null" searchable and findable
- **API Reliability:** Consistent handling across all endpoints

---

## 24. Backup and Restore Testing & Monitoring - **CRITICAL NEW**

### Current Issue
There is no regular verification that database backups are working correctly and can be successfully restored, creating a critical risk of data loss in case of system failure.

### Requirements
Implement comprehensive backup testing procedures and monitoring to ensure data recoverability.

### Implementation Details

#### A. Automated Backup Monitoring
- **Real-time Backup Status:**
  - Monitor backup job completion status
  - Alert on backup failures immediately
  - Track backup file sizes and durations
  - Verify backup integrity checksums
  - Monitor storage space for backups

- **Backup Metrics Dashboard:**
  - Last successful backup timestamp
  - Backup size trends over time
  - Success/failure rates
  - Recovery Point Objective (RPO) compliance
  - Storage usage and predictions

#### B. Regular Restore Testing
- **Scheduled Restore Tests:**
  - Weekly: Restore to test environment
  - Monthly: Full restore drill with verification
  - Quarterly: Disaster recovery simulation
  - Document restoration time for each test

- **Verification Procedures:**
  - Data integrity checks post-restore
  - Row count validations
  - Application functionality testing
  - Performance benchmarking after restore
  - User acceptance testing on restored data

#### C. Backup Strategy Enhancement
- **Backup Types:**
  - Full backups: Daily
  - Incremental backups: Hourly
  - Transaction logs: Continuous (for point-in-time recovery)
  - Off-site replication: Real-time

- **Retention Policies:**
  - Daily backups: 30 days
  - Weekly backups: 12 weeks
  - Monthly backups: 12 months
  - Yearly backups: 7 years (compliance)

### Technical Implementation

#### Monitoring Infrastructure
```yaml
backup_monitoring:
  checks:
    - backup_completion_check:
        schedule: "*/15 * * * *"  # Every 15 minutes
        alert_after_failures: 1
    - backup_size_check:
        min_size: 100MB
        max_age: 25 hours
    - backup_integrity_check:
        checksum_verification: true
        test_restore: weekly
```

#### Automated Testing Script
```bash
#!/bin/bash
# Weekly backup restore test
BACKUP_FILE=$(latest_backup)
TEST_DB="restore_test_$(date +%Y%m%d)"

# Restore backup to test database
pg_restore -d $TEST_DB $BACKUP_FILE

# Run verification queries
psql -d $TEST_DB -c "SELECT COUNT(*) FROM patients;"
psql -d $TEST_DB -c "SELECT COUNT(*) FROM therapists;"

# Check data integrity
run_integrity_checks $TEST_DB

# Report results
send_test_report $TEST_DB
```

#### Alerting Configuration
- **Critical Alerts (Immediate):**
  - Backup failure
  - Restore test failure
  - Backup storage < 20% free
  - Backup corruption detected

- **Warning Alerts (Within 1 hour):**
  - Backup taking longer than expected
  - Backup size anomaly detected
  - Scheduled test overdue

- **Information Alerts (Daily summary):**
  - Successful backup completions
  - Storage usage trends
  - Restore test results

### Recovery Procedures Documentation

#### Recovery Time Objectives (RTO)
- **Critical failure:** < 1 hour
- **Major incident:** < 4 hours
- **Standard recovery:** < 8 hours
- **Full disaster recovery:** < 24 hours

#### Recovery Point Objectives (RPO)
- **Maximum data loss:** 1 hour
- **Target data loss:** 15 minutes
- **Best case (with transaction logs):** 0 minutes

### Compliance and Audit
- **Documentation Requirements:**
  - Maintain backup/restore logs for 2 years
  - Document all restore tests and results
  - Track any backup failures and resolutions
  - Annual audit of backup procedures

- **GDPR Compliance:**
  - Encrypted backups at rest and in transit
  - Access control for backup files
  - Right to erasure implementation in backups
  - Data retention compliance

### Success Metrics
- **Backup Success Rate:** > 99.9%
- **Restore Test Success Rate:** 100%
- **Average Restore Time:** < 30 minutes
- **RPO Achievement:** 100%
- **RTO Achievement:** > 95%

### Implementation Phases

#### Phase 1: Immediate (Week 1)
- Set up basic backup monitoring
- Implement critical failure alerts
- Document current backup procedures
- Perform initial restore test

#### Phase 2: Short-term (Weeks 2-4)
- Automate restore testing
- Create monitoring dashboard
- Implement all alerting rules
- Train team on procedures

#### Phase 3: Long-term (Months 2-3)
- Optimize backup strategies
- Implement point-in-time recovery
- Set up off-site replication
- Complete disaster recovery plan

### Risk Mitigation
- **Multiple Backup Locations:** Local, cloud, and off-site
- **Different Backup Methods:** Filesystem and logical backups
- **Regular Updates:** Keep backup tools and scripts updated
- **Access Control:** Limit who can modify/delete backups
- **Encryption:** All backups encrypted with key rotation

---

## 25. Patient Excluded Therapists Removal Bug - **CRITICAL NEW**

### Current Issue
In some patients, the excluded therapists list is being unexpectedly removed. This appears to be related to partial updates from the frontend that may be overwriting the excluded therapists field with an empty value.

### Root Cause Analysis
- **Frontend Partial Updates:** When the frontend sends partial patient updates, it may be sending an empty array for excluded_therapists instead of omitting the field
- **Backend Handling:** The backend may not be differentiating between "intentionally clear this field" vs "field not included in update"
- **State Management:** Frontend state may not be properly preserving excluded therapists during other update operations

### Implementation Requirements

#### A. Backend Protection
- **Distinguish Partial Updates:**
  ```python
  def update_patient(patient_id, data):
      # Only update excluded_therapists if explicitly provided
      if 'excluded_therapists' in data:
          # Check if this is intentional clearing
          if data['excluded_therapists'] is None:
              # Log warning - suspicious clearing of exclusions
              log.warning(f"Clearing exclusions for patient {patient_id}")
          patient.excluded_therapists = data['excluded_therapists']
      # Don't touch excluded_therapists if not in update data
  ```

- **Add Validation:**
  - Require explicit confirmation to clear all exclusions
  - Log all changes to excluded therapists
  - Implement audit trail for exclusion changes

#### B. Frontend Fixes
- **Preserve Excluded Therapists in State:**
  ```javascript
  // When updating patient, preserve existing exclusions
  const updatePatient = (updates) => {
    const currentPatient = getPatientState();
    
    // Don't send excluded_therapists unless explicitly changed
    const payload = {
      ...updates,
      // Only include if intentionally modified
      ...(updates.hasOwnProperty('excluded_therapists') 
        ? { excluded_therapists: updates.excluded_therapists }
        : {})
    };
    
    return api.updatePatient(payload);
  };
  ```

- **Form Handling:**
  - Separate forms for different patient data sections
  - Don't include excluded_therapists in general update forms
  - Dedicated UI for managing exclusions

#### C. Data Recovery
- **Audit Historical Changes:**
  - Review logs to identify affected patients
  - Determine when exclusions were removed
  - Attempt to restore from backups if needed

- **Prevention Measures:**
  - Add database trigger to log exclusion changes
  - Implement soft delete for exclusions
  - Regular backup of exclusion data

### Technical Implementation
- **API Changes:**
  ```javascript
  // New endpoint for exclusion management
  PUT /api/patients/{id}/excluded-therapists
  
  // Separate from general patient update
  PATCH /api/patients/{id}  // Should not affect exclusions
  ```

- **Database Changes:**
  ```sql
  -- Audit table for tracking changes
  CREATE TABLE excluded_therapists_audit (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    therapist_id INTEGER,
    action VARCHAR(10), -- 'added' or 'removed'
    changed_by VARCHAR(255),
    changed_at TIMESTAMP,
    reason TEXT
  );
  ```

### Testing Requirements
- Unit tests for partial update handling
- Integration tests for exclusion preservation
- Frontend state management tests
- End-to-end exclusion workflow tests

### Monitoring
- Alert on bulk exclusion removals
- Track exclusion changes per patient
- Monitor API calls affecting exclusions
- Regular data integrity checks

### Success Metrics
- Zero unintended exclusion removals
- Complete audit trail for all changes
- Improved data integrity
- Reduced support tickets related to exclusions

---

## 27. Cancel Scheduled Phone Calls on Therapeutenanfrage Rejection - **NEW**

### Current Issue
When a therapeutenanfrage is rejected or cancelled, any scheduled phone calls related to that anfrage remain in the system and may still be executed, causing unnecessary work and confusion.

### Requirement
Implement automatic cancellation of scheduled phone calls when the associated therapeutenanfrage is rejected, cancelled, or otherwise terminated.

### Implementation Details

#### A. Trigger Events for Cancellation
- **Therapeutenanfrage Status Changes:**
  - Rejection by therapist (all patients rejected)
  - Cancellation by staff
  - Automatic expiration
  - Successful completion (all patients accepted)
  - Manual closure

#### B. Phone Call Management
- **Cancellation Logic:**
  ```javascript
  function cancelRelatedPhoneCalls(therapeutenanfrageId) {
    // Find all scheduled calls for this anfrage
    const scheduledCalls = getScheduledCalls({
      therapeutenanfrage_id: therapeutenanfrageId,
      status: 'scheduled'
    });
    
    // Cancel each call
    scheduledCalls.forEach(call => {
      updatePhoneCall({
        id: call.id,
        status: 'cancelled',
        cancellation_reason: 'Therapeutenanfrage rejected/cancelled',
        cancelled_at: new Date()
      });
      
      // Remove from scheduler queue
      removeFromScheduler(call.id);
    });
    
    // Log the cancellation
    logCancellation(therapeutenanfrageId, scheduledCalls.length);
  }
  ```

#### C. System Integration
- **Event Listeners:**
  - Listen for therapeutenanfrage status changes
  - Trigger phone call cancellation workflow
  - Update related records
  - Notify relevant staff

- **Database Updates:**
  ```sql
  -- Link phone calls to therapeutenanfragen
  ALTER TABLE phone_calls 
  ADD COLUMN therapeutenanfrage_id INTEGER REFERENCES therapeutenanfragen(id);
  
  -- Add cancellation tracking
  ALTER TABLE phone_calls
  ADD COLUMN cancellation_reason VARCHAR(255),
  ADD COLUMN cancelled_at TIMESTAMP;
  ```

### Technical Implementation

#### A. Backend Changes
- **Status Change Handler:**
  - Intercept therapeutenanfrage status updates
  - Check for pending phone calls
  - Execute cancellation logic
  - Send notifications

- **API Endpoints:**
  - `GET /api/therapeutenanfragen/{id}/phone-calls` - List related calls
  - `POST /api/therapeutenanfragen/{id}/cancel-calls` - Manual cancellation
  - `GET /api/phone-calls/orphaned` - Find calls without valid anfrage

#### B. Frontend Updates
- **Visual Indicators:**
  - Show linked phone calls in therapeutenanfrage view
  - Display cancellation status
  - Warning before rejecting anfrage with scheduled calls
  - Confirmation dialog for bulk cancellations

### Business Rules
- **Cancellation Conditions:**
  - Only cancel future calls (not past or in-progress)
  - Keep call history for audit purposes
  - Allow manual override to keep specific calls
  - Option to reschedule instead of cancel

- **Edge Cases:**
  - Partial rejection (some patients accepted)
  - Therapeutenanfrage reactivation
  - Multiple calls for same therapist
  - Calls already in progress

### Monitoring and Reporting
- **Metrics to Track:**
  - Number of auto-cancelled calls
  - Time saved from prevented unnecessary calls
  - Orphaned calls without valid anfrage
  - Manual override frequency

- **Alerts:**
  - Orphaned phone calls detected
  - Failed cancellation attempts
  - Unusual cancellation patterns

### User Experience Improvements
- Clear indication of linked phone calls
- Bulk actions for call management
- Undo capability within time window
- Alternative action suggestions

### Testing Requirements
- Unit tests for cancellation logic
- Integration tests for event handling
- Edge case validation
- Performance testing with bulk cancellations

### Benefits
- Reduced wasted staff time on unnecessary calls
- Cleaner scheduling system
- Better resource allocation
- Improved data consistency
- Reduced confusion and errors

---

## 28. Replace SendGrid with European Email Provider - **NEW**

### Current Issue
SendGrid, while functional, may not meet European data sovereignty requirements. Need to migrate to a GDPR-compliant European email service provider.

### Requirement
Replace SendGrid with a European-based email service provider that ensures data remains within EU borders.

### Evaluation Criteria
- **Data Sovereignty:** All data processing within EU
- **GDPR Compliance:** Full compliance with privacy regulations
- **Feature Parity:** Similar capabilities to SendGrid
- **Reliability:** High deliverability rates
- **Cost:** Competitive pricing
- **API Compatibility:** Easy migration path

### Potential European Providers
- **Mailjet** (France)
  - EU data centers
  - GDPR compliant
  - Good API documentation
  - Competitive pricing

- **Sendinblue/Brevo** (France)
  - French company, EU servers
  - Marketing automation features
  - Transactional email support
  - GDPR compliant

- **Mailgun EU** (EU Region)
  - Dedicated EU region
  - Strong deliverability
  - Developer-friendly API
  - GDPR compliant

- **SMTP2GO** (New Zealand/EU servers)
  - EU data center option
  - Simple integration
  - Good deliverability rates

### Migration Plan
- **Phase 1: Evaluation (Week 1-2)**
  - Test deliverability rates
  - API compatibility assessment
  - Cost analysis
  - Feature comparison

- **Phase 2: Implementation (Week 3-4)**
  - Set up new provider account
  - Update email service configuration
  - Implement abstraction layer
  - Update DNS records (SPF, DKIM, DMARC)

- **Phase 3: Migration (Week 5-6)**
  - Parallel running period
  - Gradual traffic migration
  - Monitor deliverability
  - Complete cutover

### Technical Implementation
- **Email Service Abstraction:**
  ```javascript
  // Abstract email provider interface
  interface EmailProvider {
    sendEmail(to, subject, content);
    sendBulkEmails(recipients, template);
    getDeliveryStatus(messageId);
  }
  
  // Provider-specific implementations
  class BrevoProvider implements EmailProvider { }
  class MailjetProvider implements EmailProvider { }
  ```

- **Configuration Updates:**
  - Environment variables for API keys
  - Provider-specific settings
  - Fallback configuration
  - Rate limiting adjustments

### Success Metrics
- Maintain 95%+ deliverability rate
- Zero data outside EU
- Cost neutral or savings
- No service interruptions
- Full GDPR compliance

---

## 29. Proton Drive as Alternative to iCloud Backup - **MEDIUM PRIORITY NEW**

### Current Issue
Currently using iCloud for data backups, which may not provide sufficient privacy guarantees and GDPR compliance for sensitive patient data.

### Requirement
Evaluate and potentially implement Proton Drive as a more privacy-focused, European-based alternative for data backups.

### Proton Drive Advantages
- **Privacy First:** End-to-end encryption by default
- **Swiss Jurisdiction:** Strong privacy laws and data protection
- **GDPR Compliant:** Full compliance with European regulations
- **Zero-Knowledge Architecture:** Proton cannot access encrypted data
- **Open Source:** Transparency in security implementation

### Comparison Matrix

| Feature | iCloud | Proton Drive |
|---------|--------|--------------|
| End-to-End Encryption | Optional | Default |
| Data Location | US/Global | Switzerland |
| GDPR Compliance | Partial | Full |
| Zero-Knowledge | No | Yes |
| Price (1TB) | €9.99/month | €9.99/month |
| API Access | Limited | Available |
| Business Features | Consumer-focused | Business plans |

### Implementation Plan

#### Phase 1: Evaluation (Week 1-2)
- **Technical Assessment:**
  - Test Proton Drive API capabilities
  - Evaluate backup/restore speeds
  - Check integration possibilities
  - Assess storage limitations

- **Security Review:**
  - Verify encryption standards
  - Review access controls
  - Audit compliance certifications
  - Test recovery procedures

#### Phase 2: Pilot Program (Week 3-4)
- Set up Proton Business account
- Implement backup scripts
- Test automated backups
- Verify restore procedures
- Monitor performance

#### Phase 3: Migration (Week 5-6)
- **Data Transfer:**
  - Parallel backup to both services
  - Verify data integrity
  - Test restore from Proton
  - Phase out iCloud gradually

### Technical Implementation
- **Backup Script Integration:**
  ```bash
  #!/bin/bash
  # Proton Drive backup script
  
  # Encrypt database dump
  pg_dump production_db | gpg --encrypt > backup.sql.gpg
  
  # Upload to Proton Drive
  proton-drive upload backup.sql.gpg /backups/
  
  # Verify upload
  proton-drive verify /backups/backup.sql.gpg
  
  # Clean old backups (keep 30 days)
  proton-drive cleanup --older-than 30d /backups/
  ```

- **Automation Setup:**
  - Scheduled daily backups
  - Automated verification
  - Alert on failures
  - Regular restore tests

### Security Considerations
- **Encryption Keys:**
  - Separate key management
  - Key rotation schedule
  - Recovery key storage
  - Multi-factor authentication

- **Access Control:**
  - Limited user access
  - Audit logging
  - IP restrictions
  - Regular access reviews

### Cost Analysis
- **Current (iCloud):** ~€120/year for 2TB
- **Proton Business:** €13/user/month (includes email, drive, calendar)
- **Additional Benefits:** Enhanced privacy, better compliance, integrated services

### Success Metrics
- Zero data breaches
- 99.9% backup success rate
- < 30 minute restore time
- Full GDPR compliance
- Reduced privacy concerns

### Risks and Mitigation
- **Service Availability:** Maintain secondary backup location
- **API Changes:** Regular monitoring and updates
- **Performance:** Test and optimize transfer speeds
- **Vendor Lock-in:** Maintain portable backup formats

---

## 31. Fix Hyphenated Name Parsing in Scraper - **LOW PRIORITY NEW**

### Current Issue
The scraper incorrectly handles therapist names with malformed hyphens (e.g., "Tietz -Roder" instead of "Tietz-Roder"), causing incorrect name splitting where the hyphenated last name is split incorrectly.

### Example Case
- **Raw Data:** "Bettina Tietz -Roder" (with space before hyphen)
- **Current (Wrong) Split:** First name: "Bettina Tietz", Last name: "-Roder"
- **Expected Result:** First name: "Bettina", Last name: "Tietz-Roder"

### Root Cause
The raw data from the 116117.de website sometimes contains inconsistent formatting with spaces before hyphens in compound last names. The current name parsing logic doesn't handle this edge case properly.

### Implementation Requirements

#### A. Data Preprocessing
- **Clean Malformed Hyphens:**
  ```python
  def clean_hyphenated_names(full_name: str) -> str:
      """
      Fix malformed hyphens in names (e.g., "Tietz -Roder" -> "Tietz-Roder")
      """
      # Remove spaces before hyphens
      cleaned = re.sub(r'\s+-', '-', full_name)
      # Remove spaces after hyphens (if any)
      cleaned = re.sub(r'-\s+', '-', cleaned)
      return cleaned
  ```

#### B. Update Name Splitting Logic
- **Enhance `_split_name` Method:**
  - Add preprocessing step before name splitting
  - Handle edge cases with hyphens at the beginning of words
  - Improve classification of hyphenated name parts

- **Code Update:**
  ```python
  def _split_name(self, full_name: str) -> Tuple[str, str]:
      if not full_name:
          return ("", "")
      
      # Remove titles
      name_without_titles = re.sub(r'(Dr\.|Prof\.|PD|Dipl\.-Psych\.) ', '', full_name)
      
      # FIX: Clean up malformed hyphens
      name_without_titles = re.sub(r'\s+-', '-', name_without_titles)
      
      # Continue with existing logic...
  ```

### Testing Requirements
- **Test Cases:**
  - "Bettina Tietz -Roder" → ("Bettina", "Tietz-Roder")
  - "Hans -Peter Müller" → ("Hans-Peter", "Müller")
  - "Marie - Claire Schmidt" → ("Marie-Claire", "Schmidt")
  - Regular hyphenated names should still work correctly

### Data Quality Improvements
- Log occurrences of malformed hyphens for monitoring
- Consider adding data quality warnings during import
- Regular audit of name formatting issues

### Priority Justification
**LOW** - This is a minor data quality issue that doesn't break functionality. Names are still imported, just with slightly incorrect splitting. The fix is simple but not critical for system operation.

### Success Metrics
- Correct parsing of all hyphenated names
- No regression in normal name parsing
- Improved data quality scores
- Reduced manual corrections needed

---

**Document Owner:** Development Team  
**Last Updated:** January 2025 (v5.3)  
**Next Review:** After critical issue resolution and implementation of high-priority items
**Changes:** 
- v5.1: Removed 3 completed items (#6, #29, #32) that were implemented in Step 3
- v5.2: Added critical distance constraint bypass bug (#30) discovered during PLZ 52159 investigation
- v5.3: Added low priority hyphenated name parsing fix (#31) for scraper data quality improvement