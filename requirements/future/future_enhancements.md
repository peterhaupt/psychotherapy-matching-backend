# Future Enhancements - Priority Items

**Document Version:** 3.0  
**Date:** January 2025  
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

## 3. Kafka/Zookeeper Stability Improvements

### Current Issue
Kafka and Zookeeper are unstable and crashing, affecting system reliability.

### Questions for Discussion
- What **type of crashes** are you seeing (out of memory, connection timeouts, data corruption, pod restarts)?
- **How frequently** are these crashes happening?
- Are you **losing data/events** when they crash, or just experiencing downtime?
- Do you need **monitoring/alerting**, **auto-restart capabilities**, or **architectural changes** (like switching to managed Kafka)?

### Potential Solutions
- Enhanced monitoring and alerting
- Auto-restart mechanisms
- Resource allocation improvements
- Consider managed Kafka services
- Circuit breaker patterns for resilience

---

## 4. Therapist Import Reporting Corrections

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

## 5. PostgreSQL Database Stability Investigation - **HIGH PRIORITY**

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

## 6. Email Delivery Testing and Verification

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

## 7. Automatic Removal of Successful Platzsuchen from Other Therapeutenanfragen - **NEW**

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

## 8. Track Successful Match Details in Platzsuche - **NEW**

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

## 9. Investigation: Unexpected Database ID Gaps in Local Production - **CRITICAL NEW**

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

## 10. Internal Server Error After Sending Patient Emails - **CRITICAL NEW**

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

## 11. Fix Therapeutenanfrage Frontend Exit Issue - **NEW**

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

## 12. Improve Patient Eligibility Criteria for Platzsuche Creation - **NEW**

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

## 13. Track Incoming Emails - **NEW**

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

## 14. Add Pagination for Therapist Selection in Vermittlung - **NEW**

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

## 15. Fix Dashboard "Ohne Aktive Platzsuche" Section - **NEW**

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

## 16. Handle Duplicate Patient Registrations During Import - **NEW**

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

## 17. Handle Duplicate Therapists with Same Email Address - **NEW**

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

## 18. Fix Missing City Data for Therapists - **NEW**

### Current Issue
Multiple therapists have missing city information in the database, which is a frequently occurring problem affecting data completeness and communication accuracy. This impacts therapist location-based searches and correspondence.

### Known Cases
- Carl-Friedolin Becker - missing city: **Roetgen**
- Evelyn Gati - missing city: **Roetgen**
- Additional cases to be identified through data audit

### Requirement
Implement a comprehensive solution to identify and fix missing city data for therapists, and prevent future occurrences.

### Implementation Details
- **Immediate Data Fix:**
  - Run database audit to identify all therapists with missing city data
  - Update known cases immediately:
    - Carl-Friedolin Becker → Roetgen
    - Evelyn Gati → Roetgen
  - Create list of all affected therapists for manual review

- **Data Validation:**
  - Add NOT NULL constraint on city field after cleanup
  - Implement validation in therapist import process
  - Add city as required field in therapist creation forms
  - Validate against list of known German cities/postal codes

- **Import Process Enhancement:**
  - Add city validation during CSV/bulk imports
  - Flag records with missing cities for review
  - Implement postal code to city lookup
  - Add data quality reports for imports

### Technical Implementation
- **Database Changes:**
  ```sql
  -- Immediate fix for known cases
  UPDATE therapists SET city = 'Roetgen' 
  WHERE name IN ('Carl-Friedolin Becker', 'Evelyn Gati');
  
  -- Find all therapists with missing cities
  SELECT id, name, street, postal_code 
  FROM therapists 
  WHERE city IS NULL OR city = '';
  ```

- **Backend Validation:**
  - Add city field validation in therapist model
  - Implement address validation service
  - Add data completeness checks

- **Frontend Changes:**
  - Make city field required in all forms
  - Add autocomplete for German cities
  - Show validation errors clearly

### Prevention Strategy
- Regular data quality audits
- Automated alerts for incomplete therapist profiles
- Import rejection for records missing required fields
- Monthly data completeness reports

---

## 19. Enhanced Support for Multi-Location Practices - **NEW**

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

## 20. Grammar Correction for Singular Patient in Therapeutenanfrage - **NEW**

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

## 21. Phone Call Templates for Patient Communication - **NEW**

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

## 22. Patient Payment Tracking System - **NEW**

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

## 23. Fix Non-Functional Automatic Reminders and Follow-up Calls - **CRITICAL NEW**

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

## 24. Fix ICD10 Diagnostic Matching Logic - **HIGH PRIORITY NEW**

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

## 25. Phone Number Display and Copy Functionality in Frontend - **NEW**

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

## Implementation Priority

| Priority | Enhancement | Complexity | Impact |
|----------|-------------|------------|--------|
| **CRITICAL** | Database ID Gap Investigation (#9) | Medium | Critical |
| **CRITICAL** | Internal Server Error After Sending Emails (#10) | Medium-High | Critical |
| **CRITICAL** | PostgreSQL Database Stability (#5) | High | Critical |
| **CRITICAL** | Handle Duplicate Patient Registrations (#16) | Medium-High | Critical |
| **CRITICAL** | Fix Non-Functional Automatic Reminders (#23) | Medium | Critical |
| **High** | Comprehensive Email Automation System (#1) | High | Very High |
| **High** | Fix ICD10 Diagnostic Matching Logic (#24) | Medium-High | High |
| **High** | Fix Missing City Data for Therapists (#18) | Low-Medium | High |
| **High** | Handle Duplicate Therapists with Same Email (#17) | Medium-High | High |
| **High** | Fix Therapeutenanfrage Frontend Exit Issue (#11) | Low | High |
| **High** | Improve Patient Eligibility Criteria (#12) | Medium | High |
| **High** | Automatic Removal of Successful Platzsuchen (#7) | Medium | High |
| **High** | Track Successful Match Details (#8) | Low-Medium | High |
| **High** | Fix Dashboard "Ohne Aktive Platzsuche" (#15) | Low-Medium | High |
| **High** | Patient Payment Tracking System (#22) | Medium-High | High |
| **High** | Phone Number Display and Copy Functionality (#25) | Low-Medium | High |
| **High** | Kafka/Zookeeper Stability (#3) | Medium-High | High |
| **High** | Email Delivery Testing and Verification (#6) | Medium | High |
| **Medium** | Enhanced Support for Multi-Location Practices (#19) | High | Medium |
| **Medium** | Grammar Correction for Singular Patient (#20) | Low | Medium |
| **Medium** | Phone Call Templates (#21) | Medium | Medium |
| **Medium** | Track Incoming Emails (#13) | High | Medium |
| **Medium** | Add Pagination for Therapist Selection (#14) | Medium | Medium |
| **Medium** | GCS Deletion Logic (#2) | Medium | Medium |
| **Medium** | Therapist Import Reporting Fix (#4) | Low-Medium | Medium |

---

## Next Steps

1. **URGENT:** Investigate database ID gaps in production environment
2. **URGENT:** Resolve internal server errors affecting email functionality
3. **URGENT:** Fix non-functional automatic reminders and follow-up systems (#23)
4. **URGENT:** Implement duplicate handling for patients (#16) to ensure data integrity
5. **URGENT:** Fix ICD10 diagnostic matching logic (#24) - review Angela Fath-Volk case
6. **URGENT:** Fix missing city data for known therapists (#18) and audit for additional cases
7. **Quick Wins:** Implement frontend fixes (#11, #15, #20, #25) and eligibility improvements (#12)
8. **Email System:** Design and implement comprehensive email automation (#1) to consolidate all email features
9. **Payment System:** Design and implement patient payment tracking (#22) for better financial management
10. **Communication:** Implement phone call templates (#21) for standardized patient communication
11. **Data Quality:** Design and implement therapist duplicate handling (#17) and multi-location support (#19)
12. **Requirements Clarification:** Schedule discussion sessions for items #2-4, #6, and #13
13. **Technical Investigation:** Deep dive into Kafka/Zookeeper issues
14. **Audit Current Systems:** Review therapist import reporting logic and email delivery
15. **Implementation Planning:** Create detailed technical specifications for high-priority items
16. **User Experience:** Prioritize items #7, #8, #11, #12, #15, #20, and #25 for immediate UX improvements

---

**Document Owner:** Development Team  
**Last Updated:** January 2025  
**Next Review:** After critical issue resolution and requirements clarification sessions