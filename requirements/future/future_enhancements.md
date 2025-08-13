# Future Enhancements - Priority Items

**Document Version:** 3.7  
**Date:** August 2025  
**Status:** Requirements Gathering (Updated)

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

### Questions for Discussion
- What **kind of therapist imports** are these (from external source, CSV uploads, API sync)?
- What specifically is wrong - **overcounting, undercounting, or wrong success/failure categorization**?
- **Where are these reports shown** (admin UI, email summaries, dashboard, logs)?
- Are the **actual imports working correctly** and it's just the reporting numbers that are wrong?

### Investigation Areas
- Audit import counting logic
- Review success/failure criteria
- Check for duplicate counting
- Validate report generation queries
- Implement import audit trail

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

## 5. Email Delivery Testing and Verification

### Requirement
Implement comprehensive testing to verify that emails are actually being sent and delivered successfully.

### Questions for Discussion
- Should we implement a **test mode** that sends emails to designated test addresses?
- Do we need **delivery confirmation tracking** (open rates, bounce handling)?
- Should we maintain an **email audit log** showing all sent emails and their status?
- What level of **integration testing** is needed for email workflows?
- Should we implement **periodic health checks** that send test emails to verify the system is working?

### Implementation Considerations
- Set up dedicated test email addresses for different email types
- Implement email delivery status tracking
- Create email sending reports and dashboards
- Add unit and integration tests for email functionality
- Consider using email testing services (e.g., Mailtrap) for development/staging
- Implement bounce and complaint handling
- Add monitoring and alerting for email delivery failures

### Related Features
- Affects Comprehensive Email Automation System
- Any future email-based features

---

## 6. Automatic Removal of Successful Platzsuchen from Other Therapeutenanfragen - **NEW**

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

## 7. Track Successful Match Details in Platzsuche - **NEW**

### Current Issue
When viewing a successful (erfolgreich) platzsuche, there's no direct way to see which therapist accepted the patient or which therapeutenanfrage led to the successful match.

### Requirement
Enhance the platzsuche model to track successful match details for better visibility and reporting.

### Implementation Details
- **New Fields in Platzsuche:**
  - `erfolgreicher_therapeut_id` - ID of the therapist who accepted the patient
  - `erfolgreiche_anfrage_id` - ID of the therapeutenanfrage that led to success
  - Additional metadata (acceptance date, trial session dates, etc.)

- **Display Enhancements:**
  - Show therapist name and contact info in successful platzsuche details
  - Link to the successful therapeutenanfrage
  - Show timeline of the successful match process

### Technical Considerations
- Database migration to add new fields
- Update the acceptance workflow to populate these fields
- Enhance API responses to include therapist details
- Update frontend to display match information
- Consider data privacy for therapist information

### Benefits
- Better tracking for reporting and analytics
- Easier follow-up and communication
- Clear audit trail of successful matches
- Improved user experience for administrators

---

## 8. Investigation: Unexpected Database ID Gaps in Local Production - **CRITICAL NEW**

### Current Issue
In the local production environment, therapeutenanfragen IDs show unexpected gaps (IDs 1-10, then jumping to 42+). This is concerning because:
- This is a **production environment** where no testing should occur
- No known deletions or rollbacks have been performed
- The gaps suggest 30+ records were somehow created and removed

### Investigation Required
- **Audit Database Logs:** Check PostgreSQL logs for DELETE operations or rolled back transactions
- **Review Application Logs:** Look for errors during anfrage creation around those missing IDs
- **Check for Automated Processes:** Identify any background jobs that might create/delete records
- **Verify Environment Isolation:** Ensure no test processes are accidentally running in production
- **Database Sequence Analysis:** Check the auto-increment sequence for anomalies

### Potential Causes to Investigate
- **Unintended Test Scripts:** Development or test scripts accidentally running against production
- **Failed Bulk Operations:** Batch imports or migrations that partially failed
- **Database Corruption:** Sequence corruption or transaction log issues
- **Unauthorized Access:** Someone manually deleting records
- **Application Bug:** Code path that creates and immediately deletes records
- **Kafka Event Issues:** Events triggering unwanted record creation/deletion

### Immediate Actions Needed
- **Enable Detailed Audit Logging:** Track all INSERT/DELETE operations on therapeutenanfragen
- **Review Access Controls:** Verify who has delete permissions in production
- **Check Cron Jobs:** Audit all scheduled tasks and background workers
- **Implement Monitoring:** Alert on unusual deletion patterns
- **Database Integrity Check:** Run PostgreSQL integrity checks
- **Review Recent Deployments:** Check if any recent code changes could cause this

### Data to Collect
- Exact time range when IDs 11-41 would have been created
- Any error logs from that time period
- Database connection logs showing which services accessed the DB
- Kafka event logs for matching-events topic
- Any manual SQL queries run against production

---

## 9. Internal Server Error After Sending Patient Emails - **CRITICAL NEW**

### Current Issue
Internal server errors are occurring intermittently after sending emails to patients, causing system instability.

### Investigation Required
- **Error Log Analysis:** Identify specific error messages and stack traces
- **Timing Analysis:** Determine if errors occur immediately after send or with delay
- **Email Type Correlation:** Check if specific types of emails trigger the error
- **Service Dependencies:** Review communication service health and dependencies
- **Resource Monitoring:** Check for memory leaks or resource exhaustion
- **Database Connection Issues:** Verify if email sending affects database connections

### Immediate Actions Needed
- **Enhanced Error Logging:** Add more detailed logging around email sending process
- **Error Handling:** Implement proper exception handling and recovery
- **Health Checks:** Add monitoring for email service health
- **Rollback Plan:** Prepare alternative email sending mechanisms
- **User Experience:** Implement user-friendly error messages

### Priority
**CRITICAL** - Affects core functionality and user experience

---

## 10. Fix Therapeutenanfrage Frontend Exit Issue - **NEW**

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

## 11. Improve Patient Eligibility Criteria for Platzsuche Creation - **NEW**

### Current Issue
When creating a new platzsuche, the patient list shows patients who are not eligible (e.g., patients without PTV11 form), making the selection process inefficient and potentially creating invalid platzsuchen.

### Requirement
Implement stricter eligibility criteria to only show patients who are truly eligible for platzsuche creation.

### Current Problems
- Patients without PTV11 form are selectable
- Criteria are too broad for practical use
- Creates unhelpful platzsuchen for ineligible patients

### Implementation Details
- **Eligibility Criteria:**
  - Must have status "Sucht Therapie"
  - Must have completed PTV11 form
  - Must not have an active platzsuche already
  - Must not have a successful (erfolgreich) platzsuche
  - Additional medical/administrative requirements (TBD)

### Technical Changes
- Update patient filtering query in platzsuche creation endpoint
- Add eligibility validation on backend
- Update frontend patient selection component
- Add clear indicators for why patients are excluded
- Implement eligibility status checking service

### User Experience
- Show only eligible patients in selection list
- Display clear reasons when patients are filtered out
- Add patient count indicators (total vs eligible)
- Provide guidance for making patients eligible

---

## 12. Track Incoming Emails - **NEW**

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

## 13. Add Pagination for Therapist Selection in Vermittlung - **NEW**

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

## 14. Fix Dashboard "Ohne Aktive Platzsuche" Section - **NEW**

### Current Issue
The dashboard section "ohne aktive Platzsuche" incorrectly includes patients with successful (erfolgreich) platzsuchen, who no longer need therapy placement.

### Requirement
Adjust the dashboard logic to exclude patients who have successfully been matched with therapists.

### Implementation Details
- **Filtering Logic:**
  - Exclude patients with platzsuche status "erfolgreich"
  - Exclude patients currently matched with therapists
  - Only show patients who genuinely need new therapy placement

- **Updated Criteria for "Ohne Aktive Platzsuche":**
  - Patients with no platzsuche at all
  - Patients with failed/cancelled platzsuchen
  - Patients with expired platzsuchen
  - Exclude patients with successful matches

### Technical Changes
- Update dashboard query logic
- Modify platzsuche status filtering
- Add proper JOIN conditions to exclude successful matches
- Update dashboard component rendering
- Add clear status indicators

### User Experience
- More accurate dashboard statistics
- Clearer understanding of patients needing help
- Reduced confusion about patient status
- Better decision-making data for staff

---

## 15. Handle Duplicate Patient Registrations During Import - **NEW**

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

## 16. Handle Duplicate Therapists with Same Email Address - **NEW**

### Current Issue
Multiple therapists working in the same practice often share the same email address, causing system conflicts and communication issues. The system needs to properly handle this common scenario.

### Requirement
Implement a solution that allows multiple therapists to share email addresses while maintaining individual therapist identities and proper communication routing.

### Implementation Details
- **Data Model Enhancement:**
  - Separate therapist personal email from practice email
  - Add fields:
    - `practice_email` - Shared practice email
    - `personal_email` - Individual therapist email (optional)
    - `is_primary_contact` - Flag for main contact at practice
    - `practice_id` - Link therapists to same practice

- **Communication Routing:**
  - For shared emails, send consolidated communications
  - Include all relevant therapists' information in emails
  - Implement email templates that handle multiple therapists
  - Add "on behalf of" functionality for practice emails

- **Duplicate Detection:**
  - Allow multiple therapists with same practice_email
  - Prevent exact duplicates (same name + same email)
  - Warn during import/creation about potential duplicates
  - Provide merge functionality for accidental duplicates

### Technical Implementation
- **Database Changes:**
  - Remove unique constraint on therapist email
  - Add composite unique constraint on (name + email)
  - Create practice table to group therapists
  - Add indexes for efficient duplicate checking

- **Import Process Updates:**
  - Enhanced duplicate detection logic
  - Automatic practice grouping based on email domain
  - Manual review interface for ambiguous cases
  - Batch processing for practice associations

- **API Changes:**
  - Update therapist creation/update endpoints
  - Add practice management endpoints
  - Modify email sending logic for grouped communications

### User Interface Enhancements
- Practice management interface
- Visual indicators for therapists in same practice
- Bulk email options for practice communications
- Clear duplicate warning messages

### Benefits
- Accurate representation of real-world practice structures
- Improved communication efficiency
- Reduced data entry errors
- Better therapist relationship management

---

## 17. Enhanced Support for Multi-Location Practices - **NEW**

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

## 18. Grammar Correction for Singular Patient in Therapeutenanfrage - **NEW**

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

## 19. Phone Call Templates for Patient Communication - **NEW**

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

## 20. Patient Payment Tracking System - **NEW**

### Current Issue
No systematic way to document whether patients have paid for services, causing billing confusion and follow-up difficulties.

### Requirement
Implement comprehensive payment tracking functionality integrated with patient records.

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

## 21. Fix Non-Functional Automatic Reminders and Follow-up Calls - **CRITICAL NEW**

### Current Issue
Automatic reminders and follow-up call scheduling features appear to be broken or non-functional, requiring manual intervention for all patient communications.

### Investigation Required
- **System Analysis:**
  - Identify which reminder types are affected
  - Check cron job/scheduler status
  - Review error logs for failed executions
  - Verify database triggers and events

- **Affected Features:**
  - PTV11 form reminders
  - Appointment reminders
  - Follow-up call scheduling
  - Status update notifications
  - Payment reminders

### Root Cause Analysis
- **Potential Issues:**
  - Scheduler service not running
  - Database connection problems
  - Email service integration failures
  - Incorrect configuration after deployment
  - Time zone handling issues
  - Queue processing failures

### Implementation Fix
- **Immediate Actions:**
  - Restart scheduler services
  - Check and fix configuration
  - Clear any blocked queues
  - Implement health checks

- **Long-term Solutions:**
  - Add monitoring and alerting
  - Implement fallback mechanisms
  - Create manual trigger options
  - Add detailed logging
  - Set up automated testing

### Testing Requirements
- Unit tests for reminder logic
- Integration tests for full workflow
- Load testing for bulk reminders
- Manual verification procedures

### Success Metrics
- Reminder delivery rate > 99%
- On-time delivery accuracy
- Reduced manual interventions
- Staff time savings

---

## 22. Fix ICD10 Diagnostic Matching Logic - **HIGH PRIORITY NEW**

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

## 23. Phone Number Display and Copy Functionality in Frontend - **NEW**

### Current Issue
Phone numbers are not easily visible or copyable in the frontend interface, making it difficult for staff to quickly contact patients and therapists.

### Requirement
Implement clear phone number display with one-click copy functionality throughout the application.

### Implementation Details
- **Display Locations:**
  - Patient detail pages
  - Therapist detail pages
  - Search results
  - Therapeutenanfrage views
  - Dashboard widgets
  - Communication history

- **Features:**
  - **Clear Formatting:** Display numbers in readable format (e.g., +49 123 456 7890)
  - **Copy Button:** One-click copy icon next to each phone number
  - **Copy Feedback:** Visual confirmation when number is copied
  - **Click-to-Call:** Option to initiate calls directly (tel: links)
  - **Mobile Detection:** Different behavior for mobile vs desktop

### Technical Implementation
- **Frontend Components:**
  ```javascript
  // Phone number component with copy functionality
  <PhoneNumber 
    number="+49 123 456 7890"
    showCopyButton={true}
    enableClickToCall={true}
  />
  ```

- **Copy Functionality:**
  - Use Clipboard API for modern browsers
  - Fallback for older browsers
  - Success/error notifications
  - Analytics tracking for usage

- **Styling:**
  - Consistent phone icon
  - Hover states for interactive elements
  - Responsive design for mobile
  - Accessibility compliance

### User Experience
- Reduce time to initiate contact
- Prevent transcription errors
- Consistent interaction pattern
- Clear visual feedback
- Mobile-friendly implementation

### Additional Features
- **Phone Number Validation:** Visual indicators for invalid numbers
- **Country Code Handling:** Automatic formatting based on country
- **History Tracking:** Log when numbers were copied/called
- **Bulk Actions:** Copy multiple numbers at once

---

## 24. Temporarily Pause Vermittlung/Platzsuche for Patient Holidays - **NEW**

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

## 25. Validate Last Psychotherapy Date in Registration Process - **NEW**

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

## 26. Set Phone Call Time to Current Time When Call is Finished - **NEW**

### Current Issue
When logging phone calls, the time of the call is not automatically set to the current time when the call is marked as finished, requiring manual time entry and potentially leading to inaccurate records.

### Requirement
Automatically capture and set the phone call timestamp to the current time when a call is marked as completed.

### Implementation Details
- **Automatic Time Capture:**
  - When "Call Finished" is clicked, automatically set timestamp
  - Option to manually adjust if needed
  - Show call duration if start time was recorded
  - Time zone handling for accurate timestamps

- **UI Enhancements:**
  - "Start Call" button to capture start time
  - "End Call" button to capture end time
  - Display call duration in real-time
  - Quick actions for common call outcomes

- **Call Tracking Features:**
  - Automatic calculation of call duration
  - Integration with phone call templates
  - Call history with accurate timestamps
  - Daily call reports for staff

### Technical Implementation
- **Database Schema:**
  ```sql
  phone_calls (
    id, patient_id, staff_id,
    call_start, call_end,
    duration_seconds,
    call_type, notes,
    template_used
  )
  ```

- **Frontend Logic:**
  ```javascript
  // Auto-set current time on call completion
  const finishCall = () => {
    const endTime = new Date();
    const duration = endTime - startTime;
    
    updateCall({
      call_end: endTime,
      duration_seconds: Math.floor(duration / 1000)
    });
  };
  ```

### Additional Features
- Integration with phone system APIs (if available)
- Automatic call logging from phone system
- Call recording references (if applicable)
- Performance metrics for call handling

---

## 27. Protection from Injection Attacks in Forms - **CRITICAL NEW**

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

## 28. Replace Google Cloud Storage with European Solution - **NEW**

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

## 29. Production Container Log Management - **NEW**

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

## 30. Backup and Restore Testing & Monitoring - **CRITICAL NEW**

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

## 31. Handle "Null" Last Name in Therapist Imports and Scraper - **HIGH PRIORITY NEW**

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

## 32. Automatic Patient Status Update to "In Therapie" - **NEW**

### Current Issue
When a platzsuche becomes successful (erfolgreich), the patient's status is not automatically updated to "In Therapie", requiring manual updates and potentially causing confusion about patient's current treatment status.

### Requirement
Implement automatic status transition when a patient is successfully matched with a therapist.

### Implementation Details
- **Trigger Event:** When platzsuche status changes to "erfolgreich"
- **Action:** Automatically update patient status from "Sucht Therapie" to "In Therapie"
- **Additional Updates:**
  - Record therapy start date
  - Link patient to assigned therapist
  - Update patient timeline
  - Send confirmation notifications

### Technical Implementation
- **Event Handler:**
  ```javascript
  // When platzsuche becomes successful
  onPlatzSucheSuccess(platzsuche) {
    const patient = getPatient(platzsuche.patient_id);
    
    updatePatient({
      id: patient.id,
      status: 'In Therapie',
      therapy_start_date: new Date(),
      therapist_id: platzsuche.erfolgreicher_therapeut_id
    });
    
    sendStatusChangeNotification(patient);
    updatePatientTimeline(patient, 'therapy_started');
  }
  ```

- **Database Changes:**
  - Add trigger or event listener for platzsuche status changes
  - Ensure transactional consistency
  - Add audit trail for status changes

### Business Rules
- Only transition from "Sucht Therapie" to "In Therapie"
- Preserve history of status changes
- Allow manual override if needed
- Handle edge cases (multiple successful matches)

### Benefits
- Accurate patient status tracking
- Reduced manual work
- Better reporting accuracy
- Clearer patient journey visualization

---

## 33. Fix Area Code Formatting Issue - **NEW**

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

## 34. Matching Service Cleanup - **NEW**

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

## 35. Replace SendGrid with European Email Provider - **NEW**

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

## Implementation Priority

| Priority | Enhancement | Complexity | Impact |
|----------|-------------|------------|--------|
| **CRITICAL** | Backup and Restore Testing & Monitoring (#30) | Medium-High | Critical |
| **CRITICAL** | Database ID Gap Investigation (#8) | Medium | Critical |
| **CRITICAL** | Internal Server Error After Sending Emails (#9) | Medium-High | Critical |
| **CRITICAL** | PostgreSQL Database Stability (#4) | High | Critical |
| **CRITICAL** | Handle Duplicate Patient Registrations (#15) | Medium-High | Critical |
| **CRITICAL** | Fix Non-Functional Automatic Reminders (#21) | Medium | Critical |
| **CRITICAL** | Protection from Injection Attacks (#27) | High | Critical |
| **High** | Handle "Null" Last Name in Imports (#31) | Medium | High |
| **High** | Comprehensive Email Automation System (#1) | High | Very High |
| **High** | Fix ICD10 Diagnostic Matching Logic (#22) | Medium-High | High |
| **High** | Handle Duplicate Therapists with Same Email (#16) | Medium-High | High |
| **High** | Fix Therapeutenanfrage Frontend Exit Issue (#10) | Low | High |
| **High** | Improve Patient Eligibility Criteria (#11) | Medium | High |
| **High** | Automatic Removal of Successful Platzsuchen (#6) | Medium | High |
| **High** | Track Successful Match Details (#7) | Low-Medium | High |
| **High** | Fix Dashboard "Ohne Aktive Platzsuche" (#14) | Low-Medium | High |
| **High** | Patient Payment Tracking System (#20) | Medium-High | High |
| **High** | Phone Number Display and Copy Functionality (#23) | Low-Medium | High |
| **High** | Email Delivery Testing and Verification (#5) | Medium | High |
| **High** | Temporarily Pause Vermittlung/Platzsuche (#24) | Medium | High |
| **High** | Validate Last Psychotherapy Date (#25) | Low-Medium | High |
| **High** | Production Container Log Management (#29) | Medium | High |
| **High** | Automatic Patient Status Update (#32) | Low-Medium | High |
| **High** | Fix Area Code Formatting (#33) | Medium | High |
| **High** | Matching Service Cleanup (#34) | High | High |
| **High** | Replace SendGrid with European Provider (#35) | Medium-High | High |
| **Medium** | Enhanced Support for Multi-Location Practices (#17) | High | Medium |
| **Medium** | Grammar Correction for Singular Patient (#18) | Low | Medium |
| **Medium** | Phone Call Templates (#19) | Medium | Medium |
| **Medium** | Track Incoming Emails (#12) | High | Medium |
| **Medium** | Add Pagination for Therapist Selection (#13) | Medium | Medium |
| **Medium** | GCS Deletion Logic (#2) | Medium | Medium |
| **Medium** | Therapist Import Reporting Fix (#3) | Low-Medium | Medium |
| **Medium** | Set Phone Call Time to Current Time (#26) | Low | Medium |
| **Medium** | Replace Google Cloud Storage (#28) | High | Medium |

---

## Next Steps

1. **IMMEDIATE - Data Protection:** Implement backup testing and monitoring (#30) to ensure data recoverability
2. **URGENT - Import Fix:** Handle "Null" last name issue (#31) affecting therapist imports and scraper
3. **URGENT - Security:** Implement injection attack protection (#27) across all forms
4. **URGENT:** Investigate database ID gaps in production environment (#8)
5. **URGENT:** Resolve internal server errors affecting email functionality (#9)
6. **URGENT:** Fix non-functional automatic reminders and follow-up systems (#21)
7. **URGENT:** Implement duplicate handling for patients (#15) to ensure data integrity
8. **URGENT:** Fix ICD10 diagnostic matching logic (#22) - review Angela Fath-Volk case
9. **Infrastructure:** Set up production log management (#29)
10. **Quick Wins:** Implement frontend fixes (#10, #14, #18, #23, #26) and eligibility improvements (#11)
11. **User Experience:** Implement pause functionality (#24) and validation improvements (#25)
12. **Email System:** Design and implement comprehensive email automation (#1)
13. **Payment System:** Design and implement patient payment tracking (#20)
14. **Communication:** Implement phone call templates (#19)
15. **Data Quality:** Design and implement therapist duplicate handling (#16) and multi-location support (#17)
16. **European Compliance:** Plan migration from Google Cloud Storage (#28) and SendGrid (#35) to European solutions
17. **Requirements Clarification:** Schedule discussion sessions for items #2-3, #5, and #12
18. **Implementation Planning:** Create detailed technical specifications for high-priority items
19. **New Features:** Implement automatic status updates (#32), fix area code formatting (#33), and cleanup matching service (#34)
20. **Audit Current Systems:** Review therapist import reporting logic and email delivery

---

**Document Owner:** Development Team  
**Last Updated:** August 2025  
**Next Review:** After critical issue resolution and requirements clarification sessions