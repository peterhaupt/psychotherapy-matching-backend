# Scraper Integration

## Summary
This document details the implementation of the data integration between the Web Scraping Service (developed in the separate [curavani_scraping](https://github.com/peterhaupt/curavani_scraping) repository) and the main Psychotherapy Matching Platform. The integration follows a local file-based approach using the file system as the exchange mechanism, enabling decoupled operation while maintaining data consistency.

## Integration Architecture

### High-Level Design

```
┌──────────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐     ┌────────────────────┐
│                      │     │                       │     │                        │     │                    │
│  Scraping Service    │────▶│  Local File System    │────▶│  Import Process        │────▶│  Therapist Service │
│  (curavani_scraping) │     │  (JSON Files)         │     │  (file monitoring)     │     │  (Core System)     │
│                      │     │                       │     │                        │     │                    │
└──────────────────────┘     └───────────────────────┘     └────────────────────────┘     └────────────────────┘
```

### Design Rationale

The local file-based integration approach was chosen for several key reasons:

1. **Operational Independence**: The scraper can operate independently of the main system, allowing for different deployment cycles and maintenance windows.

2. **Resilience**: If either system experiences downtime, data is preserved in the local file system for later processing.

3. **Auditability**: The local file system maintains a complete history of all imported data, providing an audit trail.

4. **Simplicity**: No complex API integration or real-time communications required, reducing coupling between systems.

5. **Security**: Clear boundaries with well-defined file permissions between components.

## Technical Implementation

### File Format and Schema

The integration uses JSON files with a standardized schema that includes:

1. **Metadata**: File-level information including timestamp, scrape ID, and format version
2. **Therapists**: Array of therapist data objects
3. **Statistics**: Summary metrics about the data contained in the file

Example JSON structure:

```json
{
  "metadata": {
    "timestamp": "2025-05-20T08:30:00Z",
    "scrape_id": "2025052008",
    "source": "116117.de",
    "version": "1.0"
  },
  "therapists": [
    {
      "basic_info": {
        "salutation": "Frau",
        "first_name": "Maria",
        "last_name": "Schmidt",
        "title": "Dr."
      },
      "location": {
        "street": "Hauptstraße",
        "house_number": "123",
        "postal_code": "52062",
        "city": "Aachen"
      },
      "contact": {
        "phone": "0241-12345",
        "email": "m.schmidt@praxis.de"
      },
      "therapy_methods": [
        "Verhaltenstherapie für Erwachsene",
        "Tiefenpsychologisch fundierte Psychotherapie für Erwachsene"
      ]
    }
  ],
  "statistics": {
    "total_therapists_scraped": 1250,
    "new_therapists": 15,
    "updated_therapists": 25,
    "deleted_therapists": 3,
    "unchanged_therapists": 1207
  }
}
```

### Local File System Implementation

The solution uses local file system with the following configuration:

1. **Directory Structure**:
   - Base directory configured via `THERAPIST_IMPORT_FOLDER_PATH` environment variable
   - Date subdirectories in `YYYYMMDD` format
   - Files are named by ZIP code: `{postal_code}.json`
   - Example: `/data/therapist_imports/20250520/52062.json`

2. **File Permissions**:
   - Scraper service has write permissions to the base directory
   - Main system has read permissions to all files
   - Both configured with appropriate file system permissions

3. **Data Lifecycle**:
   - Files are processed once per day by the import monitor
   - For each ZIP code, only the latest file (newest date folder) is processed
   - Processed files remain for audit purposes
   - Manual cleanup process for old files

### Import Process

The import process in the main system runs as a scheduled background thread with these steps:

1. **File Discovery**: Scans the base directory for date folders and JSON files
2. **File Selection**: For each ZIP code, selects the latest file based on date folder
3. **Validation**: Validates JSON structure and content
4. **Filtering**: Only imports therapists with adult therapy methods
5. **Deduplication**: Matches external data to existing therapists using:
   - Primary match: Same first name, last name, and PLZ
   - Secondary match: Same first name, PLZ, city, street, title, and email (for name changes)
6. **Processing**:
   - Creates new therapists for unmatched data
   - Updates existing therapists with new information
   - Preserves manually managed fields (status, availability, contact history)
7. **Error Handling**: Individual record failures don't fail the entire import
8. **Notification**: Sends email summary of import results and errors

### Data Mapping

The mapping between external therapist data and internal database structure is defined in `TherapistImporter` class with these key transformations:

1. **Personal Information**: Maps salutation, names, title from `basic_info`
2. **Location**: Combines street and house number, maps postal code and city
3. **Contact**: Maps phone, email, fax information
4. **Therapy Methods**: Converts array to single enum using logic:
   - Both VT and TP found → `egal`
   - Only TP found → `tiefenpsychologisch_fundierte_Psychotherapie`
   - Only VT found → `Verhaltenstherapie`
   - Default → `egal`
5. **Professional Data**: Maps telephone hours, languages, etc.

### Error Handling

The integration implements a robust error handling strategy:

1. **File Level**: JSON parsing errors prevent file processing
2. **Record Level**: Individual therapist errors are logged but don't stop processing
3. **Validation Errors**: Enum validation failures are logged and skipped
4. **Database Errors**: SQLAlchemy errors are caught and reported
5. **Email Notifications**: Summary emails sent for all errors
6. **Monitoring**: Import status tracked for health checks

## API Endpoints

The integration exposes the following REST endpoints:

### Import Status API
`GET /api/therapists/import-status` - Returns information about import status and statistics

### Import Health Check
`GET /health/import` - Returns health status of the import system

## Configuration

The import system is configured via environment variables:

### Required Variables
- `THERAPIST_IMPORT_FOLDER_PATH`: Base directory for import files
- `THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS`: Interval between import runs (typically 86400 for daily)

### Optional Configuration
- Managed via `shared.config` for database, communication service URLs
- Email notification settings for error reporting

## Monitoring and Alerts

The integration includes comprehensive monitoring:

1. **Import Metrics**:
   - Files processed per day
   - Therapists processed and failed counts
   - Success/failure rates
   - Processing times

2. **Health Checks**:
   - Monitor running status
   - Recent error detection
   - Failure rate monitoring
   - Inactive monitor detection (>25 hours)

3. **Error Notifications**:
   - Failed imports with detailed error reports
   - High failure rate alerts
   - System errors and exceptions

4. **Status API**: Real-time status via `/api/therapists/import-status`

## Testing Strategy

The integration is tested at multiple levels:

### Unit Tests
- Data mapping validation tests
- File processing logic tests
- Deduplication algorithm tests

### Integration Tests
- Mock file generation and processing
- Database update verification
- Error handling validation

### End-to-End Tests
- Full data flow from mock files to database
- Validation of data consistency
- Performance testing with large datasets

## Deployment Considerations

The import process is deployed with these considerations:

1. **Background Threading**: Runs as daemon thread in main application
2. **Resource Isolation**: Separate logging and error handling
3. **Maintenance Window**: Designed for continuous operation
4. **Rollback Capability**: Database transactions ensure consistency

## Security Measures

Security is implemented at multiple levels:

1. **File System Security**:
   - Proper file permissions for read/write access
   - Directory access controls

2. **Data Protection**:
   - PII handling according to GDPR requirements
   - No sensitive data in logs

3. **Input Validation**:
   - JSON schema validation
   - Field-level data validation
   - Enum value verification

4. **Audit Trail**:
   - Comprehensive logging of all operations
   - File processing history maintenance

## Future Enhancements

Planned enhancements for the integration include:

1. **Real-time Processing Option**: Add support for immediate processing of critical updates
2. **Advanced Diff Algorithm**: Improve change detection for complex field types
3. **Data Enrichment Pipeline**: Add capability to enhance data from additional sources
4. **Multi-source Support**: Extend to support multiple data sources beyond 116117.de
5. **Conflict Resolution**: Enhanced handling of concurrent updates to the same record

## Troubleshooting

Common issues and their resolutions:

| Issue | Resolution |
|-------|------------|
| Missing files | Check scraper output and file permissions |
| JSON parsing errors | Validate file structure with expected schema |
| Deduplication failures | Review matching logic in both systems |
| Performance degradation | Check file size and database indexes |
| Import monitor inactive | Check environment variables and thread status |

For detailed troubleshooting procedures, refer to the operational runbook.