# Curavani Therapist Import System Requirements & Decisions

## Overview

This document outlines the requirements and architectural decisions for implementing an automated background import system for therapist data in the Curavani microservices architecture.

**Goal**: Create an automated file processing system that continuously monitors for new therapist data files from the scraping system and imports them into the therapist service without manual intervention.

## Architecture Decision

**Selected Approach**: Background Thread Within Existing Therapist Service
- Add import monitoring code directly to existing `therapist_service`
- Background thread starts when Flask app starts
- Same process, same container, same database connections
- Chosen for simplicity and easier maintenance (following patient service pattern)

## Therapist Auto-Import System

### Requirements

**Workflow**:
1. Monitor local folder structure for new/updated JSON files from scraper
2. Process files containing therapist data arrays
3. Apply import criteria to filter relevant therapists
4. Import new therapists and update existing ones
5. Track processed files to avoid duplicate processing
6. Send error notifications on import failures

### Technical Specifications

**Monitoring**:
- **Location**: `../curavani_scraping/data/processed/YYYYMMDD/ZIPCODE.json`
- **Frequency**: Every 5 minutes (time-critical for responsive data updates)
- **File Pattern**: Date-based folders with ZIP code JSON files (e.g., `20250708/52066.json`)
- **Scope**: Multiple ZIP codes per scraping run (52062, 52064, 52066, 52068, etc.)

**Import Criteria**:
- **Filter Rule**: Only import therapists with "Erwachsene" (adults) in `therapy_methods`
- **Expected Coverage**: ~79% of therapists meet import criteria (based on sample analysis)
- **Exclusions**: Therapists working only with "Kinder und Jugendliche" (children/youth)

**Therapy Method Logic**:
- **Both types found** (Verhaltenstherapie + Tiefenpsychologisch) → `psychotherapieverfahren = "egal"`
- **Only Tiefenpsychologisch** → `psychotherapieverfahren = "tiefenpsychologisch_fundierte_Psychotherapie"`
- **Only Verhaltenstherapie** → `psychotherapieverfahren = "Verhaltenstherapie"`

**Default Values for Imported Therapists**:
- `kassensitz = True` (statutory health insurance accepted)
- `status = "aktiv"` (active status)
- `potenziell_verfuegbar = False` (not initially available)

**Processing Logic**:
- **Concurrency**: Process files sequentially to maintain data consistency
- **Data Structure**: JSON files with metadata + therapists array
- **Validation**: Use existing therapist service validation logic
- **File Tracking**: Track processed files to prevent duplicate imports

**Error Handling**:
- **On Failure**: Send email notification (similar to patient service)
- **Failed Files**: Keep local copy in failed/ folder for investigation
- **Retry Logic**: No automatic retry - manual investigation required

### Data Structure

**Expected JSON Structure**:
```json
{
  "metadata": {
    "scrape_id": "52XXX_20250708",
    "scrape_date": "2025-07-08T06:19:38.791447",
    "postcode_area": "52XXX",
    "total_therapists": 100,
    "new_therapists": 1,
    "modified_therapists": 0,
    "deleted_therapists": 1
  },
  "therapists": [
    {
      "id": "praxis26",
      "status": "new",
      "last_modified": "2025-07-08T06:19:38.791571",
      "basic_info": {
        "salutation": "Frau",
        "title": "Dr.",
        "first_name": "Ottilie",
        "last_name": "Schmitt",
        "full_name": "Ottilie Schmitt",
        "classification": "Psychotherapie: Ärztliche Psychotherapie"
      },
      "location": {
        "street": "Salierallee",
        "house_number": "15",
        "postal_code": "52066",
        "city": "Aachen"
      },
      "contact": {
        "phone": "+49 241 12345",
        "email": "dr.schmitt@example.com",
        "fax": "0241 54321"
      },
      "languages": ["Englisch"],
      "therapy_methods": [
        "Tiefenpsychologisch fundierte Psychotherapie für Erwachsene in Einzeltherapie",
        "Tiefenpsychologisch fundierte Psychotherapie für Erwachsene in Gruppentherapie"
      ]
    }
  ]
}
```

**Field Mappings**:
- `basic_info.salutation` → `anrede`
- `basic_info.title` → `titel`
- `basic_info.first_name` → `vorname`
- `basic_info.last_name` → `nachname`
- `location.street + house_number` → `strasse`
- `location.postal_code` → `plz`
- `location.city` → `ort`
- `contact.phone` → `telefon`
- `contact.email` → `email`
- `contact.fax` → `fax`
- `languages` → `fremdsprachen`

## Implementation Approach

### Integration Points

**Therapist Service** (`therapist_service/app.py`):
```python
def create_app():
    app = Flask(__name__)
    # ... existing setup ...
    
    # Start therapist import monitoring thread
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        therapist_import_thread = threading.Thread(
            target=start_therapist_import_monitor, 
            daemon=True,
            name="TherapistImportMonitor"
        )
        therapist_import_thread.start()
        app.logger.info("Therapist import monitor thread started")
    
    return app
```

### File Structure Changes

```
therapist_service/
├── imports/
│   ├── __init__.py
│   ├── file_monitor.py           # Local file system monitoring
│   ├── therapist_importer.py     # Therapist import logic and validation
│   └── import_status.py          # Status tracking (like patient service)
├── api/therapists.py             # Add import status endpoint
├── app.py                        # Modified to start import thread
└── requirements.txt              # No new dependencies needed
```

### Shared Resources

**Benefits of Background Thread Approach**:
- Reuse existing database connections and models
- Share validation logic from existing API endpoints
- Use existing configuration and logging setup
- Leverage existing Kafka event publishing
- Use existing communication service for error notifications

**Code Reuse Strategy**:
- Use existing therapist API validation functions
- Call existing CRUD logic for validation and persistence
- Publish same Kafka events as regular API operations
- Reuse communication helper functions for error notifications

## Open Questions & Decisions Needed

### 1. Therapist Identification Strategy

**Question**: How should we identify and match existing therapists?

**Options**:
- **A)** Use JSON `id` field (e.g., "praxis26") as external reference
- **B)** Match by name + location combination
- **C)** Add an `external_id` field to therapist model

**Considerations**:
- JSON `id` appears stable and unique in sample data
- Need fallback strategy if `id` changes
- Database schema impact for option C

### 2. File Processing Strategy

**Question**: Which files should be processed to avoid missing updates?

**Options**:
- **A)** Process only the latest date folder (e.g., only 20250708/)
- **B)** Process all date folders since last successful check
- **C)** Process only files newer than last processed timestamp

**Considerations**:
- Scraper may not run daily for all ZIP codes
- Need to handle gaps in scraping schedule
- Balance between completeness and performance

### 3. Change Detection

**Question**: How should we avoid re-processing identical data?

**Options**:
- **A)** Track processed files by filename + modification time
- **B)** Compare file content hash to detect actual changes
- **C)** Use JSON metadata (scrape_date, modified_therapists count)
- **D)** Combination approach

**Considerations**:
- Files may be regenerated with same content
- Need efficient way to detect meaningful changes
- Storage requirements for tracking data

### 4. Multiple ZIP Codes Processing

**Question**: How should we handle multiple ZIP codes in a single import run?

**Current Scope**: 15+ ZIP codes with 50-100 therapists each

**Options**:
- **A)** Process all ZIP codes sequentially in single thread
- **B)** Process ZIP codes in parallel (multiple threads)
- **C)** Process files individually as they're discovered

**Considerations**:
- Database transaction boundaries
- Error isolation between ZIP codes
- Processing time vs resource usage

### 5. Update Logic for Existing Therapists

**Question**: How should we handle updates to existing therapist records?

**Scenarios**:
- Therapist marked as "unchanged" but data actually differs
- Contact information updates
- Therapy method changes
- Status changes in JSON vs database

**Considerations**:
- Which fields should trigger an update?
- Should we trust JSON status field completely?
- How to handle conflicts between JSON and database state?

### 6. Database Tracking Strategy

**Question**: How should we track import progress and prevent duplicates?

**Proposed Table**:
```sql
CREATE TABLE therapist_import_tracking (
  id SERIAL PRIMARY KEY,
  file_path VARCHAR(500),           -- Relative path from monitoring root
  file_hash VARCHAR(64),            -- SHA-256 of file content
  processed_at TIMESTAMP,
  therapist_count INTEGER,
  imported_count INTEGER,
  updated_count INTEGER,
  skipped_count INTEGER,
  failed_count INTEGER,
  status VARCHAR(50),               -- 'success', 'failed', 'partial'
  error_message TEXT
);
```

**Alternative**: Use existing file modification times without database tracking

### 7. Error Notification Details

**Question**: What level of detail should error notifications include?

**Considerations**:
- Individual therapist validation errors vs file-level errors
- Include full stack traces or summary only?
- Notification frequency (immediate vs batched)
- Recipients (same as patient import errors)

### 8. Monitoring & Health Checks

**Question**: How should we monitor import system health?

**Requirements**:
- Import status endpoint (like patient service)
- Success/failure metrics
- Last successful import timestamp
- Processing lag indicators

**Proposed Endpoint**: `GET /api/therapists/import-status`

### 9. Development & Testing Strategy

**Question**: How should we handle development and testing?

**Considerations**:
- Mock data for testing import logic
- Development folder structure different from production
- Integration tests with real scraper output
- Performance testing with large files

### 10. Deployment & Configuration

**Question**: What configuration options are needed?

**Proposed Environment Variables**:
- `THERAPIST_IMPORT_FOLDER_PATH` - Base path to scraping output
- `THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS` - Check frequency (default: 300)
- `THERAPIST_IMPORT_ENABLED` - Enable/disable import (default: true)

## Next Steps

1. **Resolve Open Questions**: Make decisions on the pending questions above
2. **Design Database Changes**: Create import tracking table and any schema updates
3. **Implement Core Logic**:
   - Local file system monitoring
   - File processing and therapist filtering
   - Database import with existing validation
   - Update logic for existing therapists
4. **Add Error Handling**: Email notifications, status tracking, logging
5. **Testing**: Unit tests and integration tests with real scraper data
6. **Deployment**: Update configuration and monitor in production

## Dependencies

### Python Packages
- **No new dependencies** - uses existing file system operations and therapist service dependencies

### Database Migrations
- Create `therapist_import_tracking` table for progress tracking
- Consider adding `external_id` field to therapist table (pending decision #1)

---

*This document serves as the complete specification for implementing the Curavani therapist import system. All decisions marked as "open questions" should be resolved before beginning implementation.*