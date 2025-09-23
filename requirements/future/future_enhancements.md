# Future Enhancements - Priority Items

**Document Version:** 5.6  
**Date:** September 2025  
**Status:** Requirements Gathering (Updated - simplified email automation system to focus on weekly status updates only)

---

## Implementation Priority

| Priority | Enhancement | Complexity | Impact |
|----------|-------------|------------|--------|
| **CRITICAL** | Fix Distance Constraint Bypass Bug (#1) | Medium | Critical |
| **CRITICAL** | Backup and Restore Testing & Monitoring (#2) | Medium-High | Critical |
| **CRITICAL** | Handle Duplicate Patient Registrations (#3) | Medium-High | Critical |
| **CRITICAL** | PostgreSQL Database Stability (#4) | High | Critical |
| **High** | Analyse Duplicates of Therapists (#5) | Medium | High |
| **High** | Cancel Scheduled Phone Calls on Rejection (#6) | Medium | High |
| **High** | Handle "Null" Last Name in Imports (#7) | Medium | High |
| **Medium** | Weekly Status Updates Email Automation (#8) **[FOCUSED SCOPE]** | Medium | High |
| **High** | Fix ICD10 Diagnostic Matching Logic (#9) | Medium-High | High |
| **High** | Fix Therapeutenanfrage Frontend Exit Issue (#10) | Low | High |
| **High** | Automatic Removal of Successful Platzsuchen (#11) | Medium | High |
| **High** | Patient Payment Tracking System (#12) | Medium-High | High |
| **High** | Temporarily Pause Vermittlung/Platzsuche (#13) | Medium | High |
| **High** | Validate Last Psychotherapy Date (#14) | Low-Medium | High |
| **High** | Production Container Log Management (#15) | Medium | High |
| **Medium** | Remove Batching Logic from Communication Service (#16) | Medium | Medium |
| **Medium** | Keep Copy of Contact Form JSON on Email Failure (#17) | Medium | Medium |
| **Medium** | Enhanced Support for Multi-Location Practices (#18) | High | Medium |
| **Medium** | Grammar Correction for Singular Patient (#19) | Low | Medium |
| **Medium** | Phone Call Templates (#20) | Medium | Medium |
| **Medium** | Track Incoming Emails (#21) | High | Medium |
| **Medium** | Add Pagination for Therapist Selection (#22) | Medium | Medium |
| **Medium** | Therapist Import Reporting Fix (#23) | Low-Medium | Medium |
| **Medium** | Proton Drive Backup Alternative (#24) | Low-Medium | Medium |
| **Medium** | Fix Area Code Formatting (#25) | Medium | Medium |
| **Medium** | Matching Service Cleanup (#26) | High | Medium |
| **Low** | Add Traumatherapie Questions to FAQ (#27) | Low | Low |
| **Low** | Fix Hyphenated Name Parsing in Scraper (#28) | Low | Low |

---

## Next Steps

1. **IMMEDIATE - Critical Bug:** Fix distance constraint bypass bug (#1) that allows invalid matches when therapist city is missing
2. **IMMEDIATE - Data Protection:** Implement backup testing and monitoring (#2) to ensure data recoverability
3. **URGENT - Import Fix:** Handle "Null" last name issue (#7) affecting therapist imports and scraper
4. **URGENT:** Implement duplicate handling for patients (#3) to ensure data integrity
5. **URGENT:** Fix ICD10 diagnostic matching logic (#9) - review Angela Fath-Volk case
6. **HIGH:** Investigate and resolve therapist duplicates (#5) - check name matching logic
7. **Infrastructure:** Set up production log management (#15)
8. **Quick Wins:** Implement frontend fixes (#10) and validation improvements (#14)
9. **User Experience:** Implement pause functionality (#13)
10. **Complete Email System:** Implement weekly status updates automation (#8)
11. **Payment System:** Design and implement patient payment tracking (#12)
12. **Communication:** Implement phone call templates (#20) and cancellation logic (#6)
13. **Data Quality:** Design and implement multi-location support (#18)
14. **Code Cleanup:** Complete matching service cleanup (#26) and remove batching logic (#16)
15. **Implementation Planning:** Create detailed technical specifications for high-priority items
16. **Audit Current Systems:** Review therapist import reporting logic

---

## 1. Fix Distance Constraint Bypass Bug - **CRITICAL**

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

## 2. Backup and Restore Testing & Monitoring - **CRITICAL**

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

## 3. Handle Duplicate Patient Registrations During Import - **CRITICAL**

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

## 5. Analyse Duplicates of Therapists - **HIGH PRIORITY NEW**

### Current Issue
Multiple therapists appear to be duplicated in the system, likely due to name matching failures during import when first names were initially missing and later added.

### Specific Cases to Investigate
- **Silvina Spivak de Weissmann:** Possible compound last name parsing issue
- **Katrin Gesa Schmachtenberg:** Middle name handling
- **Carl Friedolin Becker:** Uncommon first name "Friedolin" may have been missing initially

### Root Cause Analysis
The importer likely cannot match therapists as the same person when:
- First names were missing in initial import and added later
- Uncommon first names (like "Friedolin") weren't in the common names list
- Compound last names with "de", "von", "van" are parsed differently
- Middle names are inconsistently included

### Implementation Requirements

#### A. Duplicate Detection Algorithm
- **Enhanced Matching Logic:**
  ```python
  def find_duplicate_therapists(therapist_data):
      # Match by multiple criteria
      potential_matches = []
      
      # 1. Exact email match (highest confidence)
      if therapist_data.email:
          matches = find_by_email(therapist_data.email)
          potential_matches.extend(matches)
      
      # 2. Last name + PLZ + Street (high confidence)
      if therapist_data.last_name and therapist_data.plz:
          matches = find_by_name_and_location(
              last_name=therapist_data.last_name,
              plz=therapist_data.plz,
              street=therapist_data.street
          )
          potential_matches.extend(matches)
      
      # 3. Fuzzy name matching (medium confidence)
      if therapist_data.last_name:
          matches = fuzzy_name_match(
              first_name=therapist_data.first_name,
              last_name=therapist_data.last_name,
              threshold=0.85
          )
          potential_matches.extend(matches)
      
      return deduplicate_and_score(potential_matches)
  ```

#### B. Name Matching Improvements
- **Handle Missing First Names:**
  - Don't require first name match if one record has empty first name
  - Use partial matching when first name is added later
  - Maintain history of name changes

- **Expand Common Names List:**
  - Add uncommon German first names like "Friedolin"
  - Include variations and nicknames
  - Regular updates based on import failures

#### C. Data Cleanup Process
- **Identify Existing Duplicates:**
  ```sql
  -- Find potential duplicates by last name and location
  SELECT 
      t1.id, t1.vorname, t1.nachname, t1.plz, t1.strasse,
      t2.id, t2.vorname, t2.nachname, t2.plz, t2.strasse
  FROM therapeuten t1
  JOIN therapeuten t2 ON 
      t1.nachname = t2.nachname 
      AND t1.plz = t2.plz
      AND t1.id < t2.id
  WHERE 
      (t1.vorname = '' OR t2.vorname = '' OR t1.vorname = t2.vorname)
  ORDER BY t1.nachname;
  ```

- **Merge Process:**
  - Combine data from duplicate records
  - Preserve most complete information
  - Update all references (anfragen, exclusions, etc.)
  - Maintain audit trail of merges

### Technical Implementation
- **Duplicate Prevention:**
  - Check for existing therapists before creating new
  - Use multiple matching strategies
  - Flag potential duplicates for manual review

- **Admin Interface:**
  - Duplicate detection dashboard
  - Manual merge functionality
  - Bulk processing capabilities
  - Undo/rollback options

### Success Metrics
- Reduce duplicate rate to < 1%
- Successful merge of identified duplicates
- Improved import matching accuracy
- Reduced manual cleanup effort

---

## 6. Cancel Scheduled Phone Calls on Therapeutenanfrage Rejection - **HIGH PRIORITY**

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

## 7. Handle "Null" Last Name in Therapist Imports and Scraper - **HIGH PRIORITY**

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

## 8. Weekly Status Updates Email Automation - **MEDIUM PRIORITY** [FOCUSED SCOPE]

### Overview
Implement automated weekly status update emails for patients with active therapy searches to reduce manual communication work and keep patients informed of their search progress.

### ✅ COMPLETED COMPONENTS (September 2025)

#### A. Email Infrastructure - IMPLEMENTED
- **Email Service:** Core email sending functionality operational
- **Template System:** PDF attachment system and template selection working
- **Success Notifications:** Patient notification emails when therapy found (4 template types implemented)

### 🔄 FOCUSED AUTOMATION REQUIREMENT

#### Weekly Status Update Emails
- **Trigger:** Every Monday during active search (status = "auf_der_Suche")
- **Recipients:** Patients with active platzsuchen that haven't found therapy yet
- **Content Requirements:**
  - Search progress update
  - Number of therapists contacted since last update
  - Current status of inquiries
  - Next steps and timeline expectations
  - Supportive messaging
  - Contact information for questions

- **Business Rules:**
  - Only send to patients actively searching
  - Skip if patient found therapist in past week  
  - Include opt-out option for non-critical communications
  - Stop sending after successful match or search termination
  - Respect patient communication preferences

### Implementation Details

#### A. Technical Architecture
- **Scheduler Integration:**
  - Cron job or scheduled task running every Monday
  - Query for eligible patients (active searches)
  - Generate personalized status updates
  - Track email delivery and engagement

#### B. Email Template Requirements
- **Template Location:** `shared/templates/emails/weekly_progress_update.md`
- **Dynamic Content:**
  ```markdown
  Subject: Therapy Search Update - Week {search_week} 
  
  Dear {patient_name},
  
  Here's your weekly update on your therapy search:
  
  **This Week:**
  - {therapists_contacted} therapists contacted
  - {responses_received} responses received
  - Current status: {search_status}
  
  **Next Steps:**
  - {next_actions}
  
  We continue working to find you the right therapist...
  ```

#### C. Data Requirements
- Track weekly metrics per patient:
  - Therapists contacted per week
  - Responses received
  - Search duration
  - Geographic expansion if needed
  - Historical progress

#### D. Integration Points
- **Patient Service:** Get active platzsuchen list
- **Matching Service:** Get weekly activity data
- **Communication Service:** Send emails with tracking
- **Database:** Log email delivery and responses

### Success Metrics
- **Engagement:** Email open rates > 60%
- **Satisfaction:** Reduced patient inquiries about search status
- **Efficiency:** 90% reduction in manual status update calls
- **Retention:** Maintained patient engagement during waiting periods

### Technical Implementation
- **Database Schema Updates:**
  ```sql
  -- Track weekly email status
  ALTER TABLE patient_communications 
  ADD COLUMN weekly_update_last_sent TIMESTAMP,
  ADD COLUMN weekly_update_opt_out BOOLEAN DEFAULT FALSE;
  ```

- **Scheduling Logic:**
  ```python
  def send_weekly_updates():
      # Get eligible patients (active searches, not opted out)
      patients = get_active_search_patients(
          exclude_opted_out=True,
          exclude_recently_matched=True
      )
      
      for patient in patients:
          # Generate personalized update
          update_data = generate_weekly_update(patient)
          
          # Send email
          send_email(
              template='weekly_progress_update',
              recipient=patient.email,
              data=update_data
          )
          
          # Track delivery
          log_communication(patient.id, 'weekly_update')
  ```

### GDPR Compliance
- Clear consent for weekly updates during registration
- Easy opt-out mechanism in every email
- Data retention policies for communication logs
- Right to erasure compliance

---

## 9. Fix ICD10 Diagnostic Matching Logic - **HIGH PRIORITY**

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

## 10. Fix Therapeutenanfrage Frontend Exit Issue - **HIGH PRIORITY**

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

## 11. Automatic Removal of Successful Platzsuchen from Other Therapeutenanfragen - **HIGH PRIORITY**

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

## 12. Patient Payment Tracking System - **HIGH PRIORITY**

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

## 13. Temporarily Pause Vermittlung/Platzsuche for Patient Holidays - **HIGH PRIORITY**

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

## 14. Validate Last Psychotherapy Date in Registration Process - **HIGH PRIORITY**

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

## 15. Production Container Log Management - **HIGH PRIORITY**

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

## 16. Remove Batching Logic from Communication Service - **MEDIUM PRIORITY NEW**

### Current Issue
The communication service contains unnecessary batching logic that adds complexity without providing significant benefits in the current architecture.

### Requirement
Simplify the communication service by removing batching logic and implementing direct message processing.

### Implementation Details

#### A. Current Batching Removal
- **Remove Batch Processing Code:**
  - Delete batch accumulation logic
  - Remove batch timers and thresholds
  - Eliminate batch configuration parameters
  - Clean up batch-related database tables

#### B. Direct Processing Implementation
- **Simplified Flow:**
  ```javascript
  // Current (with batching)
  function addToEmailBatch(email) {
    batch.push(email);
    if (batch.length >= BATCH_SIZE || timeSinceLastBatch > BATCH_TIMEOUT) {
      processBatch(batch);
      batch = [];
    }
  }
  
  // Simplified (direct)
  async function sendEmail(email) {
    await validateEmail(email);
    await processEmail(email);
    await logEmail(email);
  }
  ```

#### C. Performance Considerations
- Evaluate impact on email provider API limits
- Implement rate limiting if needed
- Monitor system performance after change
- Consider queuing for high-volume periods

### Benefits
- Reduced code complexity
- Easier debugging and maintenance
- Faster email delivery
- Simpler error handling
- Reduced memory usage

### Migration Plan
- Phase 1: Add feature flag for direct processing
- Phase 2: Test with subset of emails
- Phase 3: Gradual rollout
- Phase 4: Remove batching code completely

### Risk Mitigation
- Implement gradual rollout
- Monitor email delivery rates
- Keep batching code during transition
- Prepare rollback plan

---

## 17. Keep Copy of Contact Form JSON on Email Failure - **MEDIUM PRIORITY NEW**

### Current Issue
When email sending fails for contact form submissions, the data is lost and cannot be recovered or resent, leading to missed patient inquiries.

### Requirement
Implement backup storage for contact form data when email sending fails, allowing for recovery and retry.

### Implementation Details

#### A. Backup Storage Strategy
- **File System Backup:**
  ```javascript
  async function handleContactForm(formData) {
    const timestamp = Date.now();
    const filename = `contact_form_${timestamp}.json`;
    
    try {
      // Try to send email
      await sendEmail(formData);
      
      // Log success
      logSuccess(formData);
    } catch (error) {
      // Save to backup location
      await saveToBackup(filename, formData);
      
      // Log failure with backup location
      logFailure(error, filename);
      
      // Add to retry queue
      addToRetryQueue(filename);
    }
  }
  ```

#### B. Storage Implementation
- **Backup Location:**
  - Local file system directory: `/backups/failed_emails/`
  - Include metadata: timestamp, error reason, retry count
  - Implement rotation policy (keep 30 days)

- **JSON Structure:**
  ```json
  {
    "timestamp": "2025-01-15T10:30:00Z",
    "form_data": {
      "name": "Patient Name",
      "email": "patient@example.com",
      "message": "Contact form content"
    },
    "error": "SMTP connection failed",
    "retry_count": 0,
    "last_retry": null
  }
  ```

#### C. Recovery Mechanisms
- **Manual Retry Interface:**
  - Admin dashboard to view failed submissions
  - One-click retry functionality
  - Bulk retry options
  - Export to CSV for manual processing

- **Automatic Retry:**
  - Scheduled job to retry failed emails
  - Exponential backoff strategy
  - Maximum retry limit
  - Alert after final failure

### Monitoring and Alerts
- Daily summary of failed emails
- Alert on high failure rates
- Dashboard showing backup queue size
- Regular cleanup of old backups

### Success Metrics
- Zero lost contact form submissions
- Successful recovery rate > 95%
- Reduced manual intervention
- Improved customer satisfaction

---

## 18. Enhanced Support for Multi-Location Practices - **MEDIUM PRIORITY**

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

## 19. Grammar Correction for Singular Patient in Therapeutenanfrage - **MEDIUM PRIORITY**

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

## 20. Phone Call Templates for Patient Communication - **MEDIUM PRIORITY**

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

## 21. Track Incoming Emails - **MEDIUM PRIORITY**

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

## 22. Add Pagination for Therapist Selection in Vermittlung - **MEDIUM PRIORITY**

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

## 23. Therapist Import Reporting Corrections - **MEDIUM PRIORITY**

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

## 24. Proton Drive as Alternative to iCloud Backup - **MEDIUM PRIORITY**

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

## 25. Fix Area Code Formatting Issue - **MEDIUM PRIORITY**

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

## 26. Matching Service Cleanup - **MEDIUM PRIORITY**

### Current Issue
The matching service requires cleanup and optimization to remove legacy functionality and improve performance, maintainability, and reliability.

### ✅ COMPLETED COMPONENTS
- **Removed kontaktanfrage endpoint** (POST /api/platzsuchen/{id}/kontaktanfrage)
- **Updated API documentation** to remove outdated endpoint references

### 🔄 REMAINING CLEANUP TASKS

#### A. Database Schema Cleanup - HIGH PRIORITY
- **Remove Legacy Contact Request Field:**
  ```sql
  -- Remove legacy contact request field
  ALTER TABLE matching_service.platzsuche 
  DROP COLUMN IF EXISTS gesamt_angeforderte_kontakte;
  ```

- **Remove from API Responses:**
  - Remove `gesamt_angeforderte_kontakte` field from all API endpoints
  - Update response models and serializers

#### B. Error Handling Improvements - HIGH PRIORITY
- **Standardize Error Responses:**
  - Create common error response format
  - Add specific error codes for different failure scenarios
  - Improve validation error messages (currently mix English/German)

- **Files to Improve:**
  - `api/anfrage.py` - All resource classes
  - `services.py` - Cross-service communication errors
  - `algorithms/anfrage_creator.py` - Constraint validation errors

#### C. Testing Infrastructure - HIGH PRIORITY
- **Test Coverage Needed:**
  - Unit tests for algorithm functions
  - Integration tests for API endpoints
  - Mock tests for cross-service communication

- **Test Scenarios:**
  - Therapist selection with various PLZ prefixes
  - Constraint validation (distance, preferences, exclusions)
  - Inquiry creation and response handling
  - Error conditions and edge cases

#### D. Configuration Centralization - MEDIUM PRIORITY
- **Centralize Hard-coded Values:**
  ```python
  # shared/config.py additions needed
  ANFRAGE_CONFIG = {
      'min_size': 1,  # Make configurable
      'max_size': 6,
      'plz_match_digits': 2,
      'default_max_distance_km': 25,
      'cooling_period_weeks': 4  # Currently hard-coded
  }
  ```

- **Files to Update:**
  - `algorithms/anfrage_creator.py` - Use config for all constants
  - `models/therapeutenanfrage.py` - Dynamic constraint validation
  - `services.py` - Use config for cooling periods

#### E. Code Cleanup - MEDIUM PRIORITY
- **Bundle Terminology References:**
  - Update comments in `algorithms/anfrage_creator.py`
  - Field comment "renamed from bundle" in `models/therapeut_anfrage_patient.py`
  - Comments about "Bundle/Bündel" in `api/__init__.py`

- **Inquiry Size Validation Decision:**
  - Current constraint: `anfragegroesse >= 3 AND anfragegroesse <= 6`
  - API documentation states minimum is 1
  - **Decision needed:** Update constraint to >= 1 or update docs to >= 3

#### F. Performance Optimizations - LOW PRIORITY
- **Optimization Opportunities:**
  - `GET /platzsuchen` - Batch patient data fetching
  - `GET /therapeutenanfragen` - Batch therapist data fetching
  - Database query optimization for large datasets
  - Caching for frequently accessed therapist data

### Implementation Priority Matrix

| Priority | Component | Effort | Risk | Business Impact |
|----------|-----------|--------|------|-----------------|
| **High** | Remove gesamt_angeforderte_kontakte | Medium | Low | Medium (Code clarity) |
| **High** | Error Handling Standardization | Medium | Low | High (User experience) |
| **High** | Testing Infrastructure | High | Low | High (Quality assurance) |
| **Medium** | Configuration Centralization | Medium | Medium | Medium (Maintainability) |
| **Medium** | Bundle References Cleanup | Low | Low | Low (Code clarity) |
| **Low** | Inquiry Size Validation | Low | Medium | Low (Business rule clarity) |
| **Low** | Performance Optimizations | High | Medium | Low (Current scale) |

### Migration Requirements
- **Database Migration:** Required for removing `gesamt_angeforderte_kontakte` column
- **API Breaking Changes:** 
  - Removing field from responses is a breaking change
  - Consider API versioning or deprecation period
- **Testing:** Comprehensive testing after each cleanup phase

### Success Metrics
- Reduced code complexity
- Improved error handling consistency
- 80%+ test coverage
- Centralized configuration
- Better maintainability scores

---

## 27. Add Traumatherapie Questions to FAQ - **LOW PRIORITY NEW**

### Current Issue
The FAQ section on www.curavani.com is missing important information about Traumatherapie (trauma therapy), which is a common patient inquiry.

### Requirement
Add comprehensive Traumatherapie-related questions and answers to the FAQ section.

### FAQ Content to Add
- **What is Traumatherapie?**
  - Definition and explanation
  - Types of trauma addressed
  - When it's recommended

- **How does Curavani help with finding trauma therapists?**
  - Specialized matching process
  - Therapist qualifications
  - Additional screening criteria

- **What trauma therapy methods are available?**
  - EMDR
  - Trauma-focused CBT
  - Somatic approaches
  - Other evidence-based methods

- **How long does trauma therapy typically take?**
  - Timeline expectations
  - Factors affecting duration
  - Insurance coverage considerations

- **What qualifications should trauma therapists have?**
  - Required certifications
  - Specialized training
  - Experience requirements

### Implementation Details
- Update FAQ page content
- Add new section for Traumatherapie
- Ensure SEO optimization
- Include internal links to relevant pages
- Consider adding patient testimonials

### Content Guidelines
- Use clear, non-technical language
- Provide helpful, accurate information
- Include disclaimers where appropriate
- Link to professional resources

### Success Metrics
- Reduced support inquiries about trauma therapy
- Improved page engagement metrics
- Better SEO ranking for trauma-related searches
- Increased patient confidence

---

## 28. Fix Hyphenated Name Parsing in Scraper - **LOW PRIORITY**

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
**Last Updated:** September 2025 (v5.6)  
**Next Review:** After critical issue resolution and implementation of high-priority items
**Changes:** 
- v5.6: Simplified Item #8 to focus only on weekly status updates automation, removing completed and unwanted email automation categories based on user requirements
