# Scraping Service Architecture

## Overview

This document outlines the architecture and implementation approach for the 116117.de scraping service for the Psychotherapy Matching Platform. The scraping service will operate as a separate system in a different cloud environment while maintaining integration with the main microservice architecture.

```
┌──────────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐     ┌────────────────────┐
│                      │     │                       │     │                        │     │                    │
│  Scraping Service    │────▶│  Cloud Storage Bucket │────▶│  Import Process        │────▶│  Therapist Service │
│  (Independent)       │     │  (JSON Files)         │     │  (in main architecture)│     │  (Core System)     │
│                      │     │                       │     │                        │     │                    │
└──────────────────────┘     └───────────────────────┘     └────────────────────────┘     └────────────────────┘
```

## Scraping Service Responsibilities

The scraping service operates independently with the following responsibilities:

1. **Data Collection**: Scrape therapist data from arztsuche.116117.de at regular intervals
2. **Data Processing**: Normalize and validate the collected data
3. **Diff Generation**: Compare with previous scrapes to identify new, updated, and deleted therapists
4. **File Generation**: Create structured JSON files containing therapist data changes
5. **Storage**: Upload files to a cloud storage bucket with timestamped filenames

## Cloud Storage Integration

The integration between the systems uses cloud storage as an intermediary:

1. **Storage Format**: 
   - JSON files with consistent schema
   - Filename pattern: `therapists_YYYYMMDD_HHMMSS.json`
   - Each file contains only changes since the last scrape (additions, modifications, deletions)

2. **File Structure**:
   ```json
   {
     "timestamp": "2025-05-14T08:30:00Z",
     "scrape_id": "2025051408",
     "additions": [...],
     "modifications": [...],
     "deletions": [...]
   }
   ```

3. **Authentication**:
   - Service account with read-only access for the main system
   - Service account with write access for the scraping service

## Import Process

The import process in the main architecture:

1. **Scheduled Job**: Runs daily (or on demand) to check for new files
2. **Authentication**: Authenticates to the cloud storage bucket
3. **Processing**: 
   - Finds the latest unprocessed file
   - Applies changes to the therapist database
   - Records the import in a processing log
4. **Validation**: Validates all imported data before committing changes
5. **Notifications**: Notifies administrators of significant changes

## Advantages

This architecture provides several advantages:

1. **Separation of Concerns**: Scraping service is fully decoupled from the main system
2. **Operational Independence**: Each system can be maintained, deployed, and scaled independently
3. **Resilience**: If either system is temporarily unavailable, data isn't lost
4. **Auditability**: Complete history of all scraped data is preserved
5. **Simplicity**: No complex API integration or real-time communications required
6. **Cost-Effective**: Cloud storage is inexpensive for this use case

## Implementation Guidelines

### Scraping Service Repository Structure

```
scraping-service/
├── .github/             # CI/CD workflows
├── src/
│   ├── scrapers/        # Scraper implementation
│   ├── processors/      # Data processing modules
│   ├── storage/         # Cloud storage interaction
│   ├── models/          # Data models and schemas
│   ├── diff/            # Diff generation
│   └── main.py          # Entry point
├── tests/               # Test suite
├── config/              # Configuration files
├── Dockerfile           # Container definition
├── requirements.txt     # Dependencies
└── README.md            # Documentation
```

### Main System Import Implementation

The import component should:

1. Use Google Cloud Storage client libraries for authentication and file access
2. Implement idempotent processing (safe to run multiple times)
3. Keep detailed logs of all imported changes
4. Include error handling and recovery mechanisms
5. Provide administrative interface for manual imports when needed

## Security Considerations

1. **Authentication**: Use service accounts with limited permissions
2. **Data Protection**: Ensure sensitive data is handled according to applicable regulations
3. **Bucket Permissions**: Restrict access using the principle of least privilege
4. **Data Validation**: Always validate imported data for consistency and security
5. **Monitoring**: Implement monitoring for unexpected data changes

## Future Enhancements

1. **Notification System**: Alerts for significant changes or errors
2. **Import API**: Optional API endpoint for manual triggers
3. **Data Enrichment**: Additional data sources to enhance therapist profiles
4. **Change Approval**: Administrative approval process for certain changes
5. **Advanced Diff Algorithm**: Improved change detection and conflict resolution