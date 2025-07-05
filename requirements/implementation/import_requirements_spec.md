# Curavani Import System Requirements & Decisions

## Overview

This document outlines the requirements and architectural decisions for implementing automated background import systems for both patient and therapist data in the Curavani microservices architecture.

**Goal**: Create automated file processing systems that continuously monitor for new data files and import them into the respective services without manual intervention.

## Architecture Decision

**Selected Approach**: Option 1 - Background Threads Within Existing Services
- Add import monitoring code directly to existing `patient_service` and `therapist_service`
- Background threads start when Flask apps start
- Same process, same container, same database connections
- Chosen for simplicity and easier maintenance

## Patient Auto-Import System

### Requirements

**Workflow**:
1. Monitor Google Cloud Storage (GCS) bucket continuously 
2. Download new JSON files from GCS bucket
3. Store local copy of JSON file (for backup purposes)
4. Import patient data into database
5. After successful storage and import → delete JSON file from GCS bucket

### Technical Specifications

**Monitoring**:
- **Frequency**: Hourly checks (not time-critical)
- **GCS Bucket**: `curavani-production-data-transfer`
- **File Pattern**: `{lastname}_{firstname}_{date}_{token}.json` (based on verify_token.php)

**Local Storage**:
- **Location**: Permanent storage accessible by host system (for backups)
- **Suggested Path**: `/var/lib/postgresql/data/patient_imports/` or similar
- **Purpose**: Include JSON files in host system backups

**Processing**:
- **Concurrency**: Process one file at a time (sequential processing)
- **Data Structure**: Complex nested JSON with `patient_data` + `consent_metadata` sections
- **Validation**: Use existing patient service validation logic
- **Duplicate Detection**: Match on email + name combination

**Error Handling**:
- **On Failure**: Keep cloud file, send email to `info@curavani.com`
- **Retry Logic**: TBD (open question)

### Data Structure Example

```json
{
    "patient_data": {
        "anrede": "Herr",
        "geschlecht": "männlich",
        "vorname": "Max",
        "nachname": "Mustermann",
        "geburtsdatum": "2000-01-01",
        // ... additional patient fields
    },
    "consent_metadata": {
        "ip_address": "37.201.29.143",
        "user_agent": "Mozilla/5.0...",
        "timestamp_utc": "2025-07-05T14:33:55Z",
        // ... consent tracking data
    },
    "registration_timestamp": "2025-07-05 14:33:55",
    "registration_token": "0b1ab67b"
}
```

## Therapist Auto-Import System

### Requirements

**Workflow**:
1. Monitor local folders for new JSON files from scraper
2. Import therapists from JSON file
3. Check if therapist is new → import
4. Check if therapist exists → compare for updates
5. Track which therapists/files have been processed

### Technical Specifications

**Monitoring**:
- **Location**: Local file system folders
- **File Pattern**: ZIP code based (e.g., `52074.json`)
- **Frequency**: Weekly bulk imports (100+ therapists per file)

**Processing Logic**:
- **File Tracking**: Database table to track processed files
- **Therapist Identification**: Use `"id": "praxis67"` field as unique identifier
- **Status Processing**: Handle `"new"`, `"modified"`, `"unchanged"`, `"deleted"` statuses
- **Update Detection**: Complex logic needed (open question)

**File Management**:
- **After Processing**: Keep files (no deletion)
- **Duplicate Prevention**: Track processed files in database

### Data Structure Example

```json
{
  "metadata": {
    "scrape_id": "52XXX_20250702",
    "scrape_date": "2025-07-02T03:13:24.425211",
    "postcode_area": "52XXX",
    "total_therapists": 100,
    "new_therapists": 0,
    "modified_therapists": 1,
    "deleted_therapists": 0
  },
  "therapists": [
    {
      "id": "praxis67",
      "status": "modified",
      "last_modified": "2025-07-02T03:13:24.425333",
      "basic_info": {
        "salutation": "Herr",
        "first_name": "Thomas",
        "last_name": "Zeevaert",
        // ... additional therapist data
      }
    }
  ]
}
```

## Implementation Approach

### Integration Points

**Patient Service** (`patient_service/app.py`):
```python
def create_app():
    app = Flask(__name__)
    # ... existing setup ...
    
    # Start patient import monitoring thread
    patient_import_thread = threading.Thread(
        target=start_patient_import_monitor, 
        daemon=True
    )
    patient_import_thread.start()
    
    return app
```

**Therapist Service** (`therapist_service/app.py`):
```python
def create_app():
    app = Flask(__name__)
    # ... existing setup ...
    
    # Start therapist import monitoring thread
    therapist_import_thread = threading.Thread(
        target=start_therapist_import_monitor, 
        daemon=True
    )
    therapist_import_thread.start()
    
    return app
```

### Shared Resources

**Benefits of Background Thread Approach**:
- Reuse existing database connections and models
- Share validation logic from existing API endpoints
- Use existing configuration and logging setup
- Leverage existing Kafka event publishing

**Code Reuse Strategy**:
- Import endpoints extract and transform data
- Call existing CRUD logic for validation and persistence
- Publish same Kafka events as regular API operations

## Open Questions & Decisions Needed

### Patient Import System

1. **Duplicate Detection Logic**:
   - Should matching email+name update existing patient or skip?
   - How to handle partial matches (same email, different name)?

2. **Consent Metadata Storage**:
   - Store full `consent_metadata` section in database?
   - Or just log it and store only `patient_data`?
   - Create separate consent tracking table?

3. **File Naming Validation**:
   - Should we validate the filename pattern strictly?
   - What to do with files that don't match expected pattern?

4. **Error Recovery**:
   - Retry failed imports automatically?
   - How many retries before giving up?
   - Dead letter queue for permanently failed files?

### Therapist Import System

5. **Local Folder Structure**:
   - Specific folder path to monitor?
   - Should we monitor subdirectories?
   - File naming convention validation?

6. **Therapist Matching Strategy**:
   - Is `praxis67` style ID always unique and stable?
   - Fallback matching if ID changes (name + address)?

7. **Update Detection Logic**:
   - Which fields should trigger an update?
   - Ignore `last_modified` timestamp for comparison?
   - Deep comparison of nested objects (contact, therapy_methods)?

8. **Database Tracking Table Design**:
   ```sql
   CREATE TABLE import_tracking (
     id SERIAL PRIMARY KEY,
     file_name VARCHAR(255),
     file_hash VARCHAR(64),        -- To detect file changes
     processed_at TIMESTAMP,
     therapist_count INTEGER,
     new_count INTEGER,
     updated_count INTEGER,
     status VARCHAR(50)            -- 'success', 'failed', 'partial'
   );
   ```

9. **Status Field Handling**:
   - Should `"unchanged"` status skip processing entirely?
   - How to handle `"deleted"` status therapists?
   - What if status doesn't match actual data changes?

### General Implementation

10. **Logging Strategy**:
    - Log level for import operations?
    - Separate log files for import vs API operations?
    - Structured logging format for monitoring?

11. **Monitoring & Alerting**:
    - Health checks for import threads?
    - Metrics to track (import success rate, processing time)?
    - Alert thresholds for failed imports?

12. **Performance Considerations**:
    - Batch size for database operations?
    - Rate limiting for GCS API calls?
    - Memory usage for large therapist files?

13. **Development & Testing**:
    - Mock GCS bucket for development?
    - Test data fixtures for both import types?
    - Integration test strategy?

## Next Steps

1. **Resolve Open Questions**: Make decisions on the pending questions above
2. **Design Database Changes**: Create import tracking tables and any new patient fields
3. **Implement Core Logic**: 
   - GCS monitoring and download
   - File processing and validation
   - Database import with existing validation
4. **Add Error Handling**: Email notifications, retry logic, logging
5. **Testing**: Unit tests and integration tests with mock data
6. **Deployment**: Update Docker configurations and deployment scripts

## File Structure Changes

### Patient Service
```
patient_service/
├── imports/
│   ├── __init__.py
│   ├── gcs_monitor.py      # GCS bucket monitoring
│   ├── patient_importer.py # Patient import logic
│   └── file_processor.py   # File download/storage
├── app.py                  # Modified to start import thread
└── requirements.txt        # Add GCS dependencies
```

### Therapist Service
```
therapist_service/
├── imports/
│   ├── __init__.py
│   ├── file_monitor.py        # Local file monitoring
│   ├── therapist_importer.py  # Therapist import logic
│   └── import_tracker.py      # Database tracking
├── app.py                     # Modified to start import thread
└── requirements.txt           # No new dependencies needed
```

## Dependencies

### New Python Packages
- **Patient Service**: `google-cloud-storage` for GCS access
- **Therapist Service**: No new dependencies (uses existing file system operations)

### Database Migrations
- Create import tracking table for therapist service
- Potentially add consent metadata table for patient service (TBD)

---

*This document serves as the complete specification for implementing the Curavani import systems. All decisions marked as "open questions" should be resolved before beginning implementation.*