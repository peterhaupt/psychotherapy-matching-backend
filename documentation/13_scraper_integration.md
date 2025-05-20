# Scraper Integration

## Summary
This document details the implementation of the data integration between the Web Scraping Service (developed in the separate [curavani_scraping](https://github.com/peterhaupt/curavani_scraping) repository) and the main Psychotherapy Matching Platform. The integration follows a file-based approach using cloud storage as the exchange mechanism, enabling decoupled operation while maintaining data consistency.

## Integration Architecture

### High-Level Design

```
┌──────────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐     ┌────────────────────┐
│                      │     │                       │     │                        │     │                    │
│  Scraping Service    │────▶│  Cloud Storage Bucket │────▶│  Import Process        │────▶│  Therapist Service │
│  (curavani_scraping) │     │  (JSON Files)         │     │  (in main architecture)│     │  (Core System)     │
│                      │     │                       │     │                        │     │                    │
└──────────────────────┘     └───────────────────────┘     └────────────────────────┘     └────────────────────┘
```

### Design Rationale

The file-based integration approach was chosen for several key reasons:

1. **Operational Independence**: The scraper can operate independently of the main system, allowing for different deployment cycles and maintenance windows.

2. **Resilience**: If either system experiences downtime, data is preserved in the storage layer for later processing.

3. **Auditability**: The cloud storage bucket maintains a complete history of all imported data, providing an audit trail.

4. **Simplicity**: No complex API integration or real-time communications required, reducing coupling between systems.

5. **Security**: Clear boundaries with well-defined authentication and authorization between components.

## Technical Implementation

### File Format and Schema

The integration uses JSON files with a standardized schema that includes:

1. **Metadata**: File-level information including timestamp, scrape ID, and format version
2. **Changes**: Three categories of changes (additions, modifications, deletions)
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
  "changes": {
    "additions": [...],
    "modifications": [...],
    "deletions": [...]
  },
  "statistics": {
    "total_therapists_scraped": 1250,
    "new_therapists": 15,
    "updated_therapists": 25,
    "deleted_therapists": 3,
    "unchanged_therapists": 1207
  }
}
```

### Cloud Storage Implementation

The solution uses cloud storage with the following configuration:

1. **Bucket Structure**:
   - Root directory contains all therapist data files
   - Files are named with timestamp pattern: `therapists_YYYYMMDD_HHMMSS.json`
   - Additional metadata is stored in cloud storage object attributes

2. **Authentication**:
   - Scraper uses a service account with write-only permissions
   - Main system uses a service account with read-only permissions
   - Both are configured with least-privilege principles

3. **Data Lifecycle**:
   - Files are retained for 90 days by default
   - A separate archival process moves older files to cold storage
   - Processed files are marked with custom metadata for tracking

### Import Process

The import process in the main system runs as a scheduled job with these steps:

1. **File Discovery**: Checks for new files in the storage bucket
2. **File Selection**: Selects the latest unprocessed file based on timestamp
3. **Validation**: Validates JSON structure and content
4. **Differential Processing**:
   - Processes additions of new therapists
   - Applies modifications to existing therapists
   - Handles deletions with appropriate business logic
5. **Reconciliation**: Matches external IDs to internal database records
6. **Commit**: Applies changes in a single transaction for consistency
7. **Status Update**: Updates the file metadata to mark as processed

### Data Mapping

The mapping between external therapist data and internal database structure is defined in `TherapistMapper` class with these key transformations:

1. **ID Handling**: External IDs are stored alongside internal IDs for reference
2. **Data Normalization**: Address information is standardized for geocoding
3. **Availability Parsing**: Text-based availability is converted to structured JSON
4. **Contact Enrichment**: Phone and email information is extracted and formatted

### Error Handling

The integration implements a robust error handling strategy:

1. **Transaction Management**: All database updates occur in a single transaction
2. **Partial Failures**: Individual record failures don't fail the entire import
3. **Error Categorization**:
   - Schema validation errors
   - Data format errors
   - Business rule violations
   - System errors
4. **Retry Logic**: Automatic retry for transient errors
5. **Manual Intervention**: Clear workflow for handling non-recoverable errors

## API Endpoints

The integration exposes the following REST endpoints:

### Import Status API
`GET /api/scraper-imports` - Returns information about previous imports

### Manual Import Trigger
`POST /api/scraper-imports/trigger` - Manually triggers an import process

### Import Details 
`GET /api/scraper-imports/{import_id}` - Returns detailed information about a specific import

## Testing Strategy

The integration is tested at multiple levels:

### Unit Tests
- Schema validation tests
- Data mapper tests
- File processing logic tests

### Integration Tests
- Mock file generation and processing
- Cloud storage interaction tests
- Database update verification

### End-to-End Tests
- Full data flow from mock scraper to database
- Validation of data consistency
- Performance testing with large datasets

## Monitoring and Alerts

The integration includes comprehensive monitoring:

1. **Import Metrics**:
   - Success/failure rates
   - Processing times
   - Record counts by type

2. **Data Quality Metrics**:
   - Schema validation errors
   - Data format issues
   - Outlier detection

3. **Operational Alerts**:
   - Failed imports
   - Missing scheduled imports
   - Unusual data volume changes

4. **Dashboard**: Centralized monitoring dashboard with all key metrics

## Deployment Considerations

The import process is deployed with these considerations:

1. **Scaling**: Horizontally scalable to handle large import volumes
2. **Resource Isolation**: Runs in a dedicated container to prevent resource contention
3. **Maintenance Window**: Scheduled to run during off-peak hours
4. **Rollback Capability**: Ability to revert to previous state if needed

## Security Measures

Security is implemented at multiple levels:

1. **Transport Security**:
   - TLS encryption for all data transfers
   - Secure API endpoints with authentication

2. **Storage Security**:
   - Encryption at rest for all data
   - Access controls with fine-grained permissions

3. **Data Protection**:
   - PII handling according to GDPR requirements
   - Data minimization practices

4. **Audit Trail**:
   - Comprehensive logging of all operations
   - Immutable audit records for compliance

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
| Missing files | Check scraper logs and authentication permissions |
| Schema validation errors | Compare file structure with expected schema |
| ID reconciliation failures | Verify external ID mapping logic |
| Performance degradation | Check file size and database indexes |
| Duplicate records | Review identification logic in both systems |

For detailed troubleshooting procedures, refer to the operational runbook.
