# Future Enhancements - Priority Items

**Document Version:** 2.0  
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

## Implementation Priority

| Priority | Enhancement | Complexity | Impact |
|----------|-------------|------------|--------|
| **CRITICAL** | PostgreSQL Database Stability | High | Critical |
| **High** | Patient Import Email Notifications | Low | Medium |
| **High** | Kafka/Zookeeper Stability | Medium-High | High |
| **Medium** | GCS Deletion Logic | Medium | Medium |
| **Medium** | Therapist Import Reporting Fix | Low-Medium | Medium |
| **Low** | Weekly Patient Status Emails | Medium | Low |

---

## Next Steps

1. **Requirements Clarification:** Schedule discussion sessions for items 2-5
2. **Technical Investigation:** Deep dive into Kafka/Zookeeper issues
3. **Audit Current Systems:** Review therapist import reporting logic
4. **Implementation Planning:** Create detailed technical specifications

---

**Document Owner:** Development Team  
**Last Updated:** January 2025  
**Next Review:** After requirements clarification sessions