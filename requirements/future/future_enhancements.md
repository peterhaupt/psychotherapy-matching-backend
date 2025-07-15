# Future Enhancements - Priority Items

**Document Version:** 2.2  
**Date:** January 2025  
**Status:** Requirements Gathering

---

## 1. Email Notifications for Patient Imports from GCS

### Requirement
Send an email notification to `info@curavani.com` for each new patient successfully imported from GCS.

### Specification
- **Trigger:** One email per patient imported
- **Recipient:** `info@curavani.com`
- **Email Content:**
  - Patient name
  - Import timestamp
  - File source (GCS bucket/path)
  - Validation status

### Implementation Notes
- Email should be sent after successful import to patient-service
- Use existing communication service for email delivery
- Consider email template for consistent formatting
- Add configuration option to enable/disable notifications

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

## 4. Weekly Patient Status Emails

### Requirement
Implement weekly email updates to patients about their platzsuche status and progress.

### Questions for Discussion
- Should this go to **all patients** or only those with **active platzsuchen**?
- What **status information** should be included (search progress, therapist contacts made, next steps)?
- What **day of the week** should these go out?
- Should patients be able to **opt out** of these emails?
- How should **multiple active searches** for the same patient be handled?

### Implementation Considerations
- Email template design
- Opt-out mechanism
- Scheduling system
- Patient communication preferences
- GDPR compliance for automated emails

---

## 5. Therapist Import Reporting Corrections

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

## 6. PostgreSQL Database Stability Investigation - **HIGH PRIORITY**

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

## 7. Email Delivery Testing and Verification

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
- Affects Item #1 (Patient Import Notifications)
- Affects Item #4 (Weekly Patient Status Emails)
- Any future email-based features

---

## 8. Automatic Removal of Successful Platzsuchen from Other Therapeutenanfragen - **NEW**

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

## 9. Track Successful Match Details in Platzsuche - **NEW**

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

## Implementation Priority

| Priority | Enhancement | Complexity | Impact |
|----------|-------------|------------|--------|
| **CRITICAL** | PostgreSQL Database Stability | High | Critical |
| **High** | Automatic Removal of Successful Platzsuchen (#8) | Medium | High |
| **High** | Track Successful Match Details (#9) | Low-Medium | High |
| **High** | Patient Import Email Notifications | Low | Medium |
| **High** | Kafka/Zookeeper Stability | Medium-High | High |
| **High** | Email Delivery Testing and Verification | Medium | High |
| **Medium** | GCS Deletion Logic | Medium | Medium |
| **Medium** | Therapist Import Reporting Fix | Low-Medium | Medium |
| **Low** | Weekly Patient Status Emails | Medium | Low |

---

## Next Steps

1. **Requirements Clarification:** Schedule discussion sessions for items 2-5 and 7
2. **Technical Investigation:** Deep dive into Kafka/Zookeeper issues
3. **Audit Current Systems:** Review therapist import reporting logic and email delivery
4. **Implementation Planning:** Create detailed technical specifications
5. **Quick Wins:** Prioritize items #8 and #9 as they directly improve user experience

---

**Document Owner:** Development Team  
**Last Updated:** January 2025  
**Next Review:** After requirements clarification sessions