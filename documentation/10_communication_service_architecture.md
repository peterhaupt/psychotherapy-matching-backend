# Communication Service Architecture

## Overview

The Communication Service is responsible for managing all interaction with therapists, including email communication and phone call scheduling. Following recent architectural changes, the service has been simplified to focus solely on sending communications, with all bundle logic moved to the Matching Service.

## System Architecture

### High-Level Architecture (Simplified)

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Communication Service                           │
│                                                                      │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ Email Manager  │   │  Email Queue   │   │ Phone Call         │   │
│  │                │   │  Manager       │   │ Scheduler          │   │
│  │                │   │                │   │                    │   │
│  └────────┬───────┘   └───────┬────────┘   └──────────┬─────────┘   │
│           │                   │                       │              │
│           ▼                   ▼                       ▼              │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐   │
│  │                │   │                │   │                    │   │
│  │ Template       │   │ Robust Kafka   │   │ Call Tracking &    │   │
│  │ Engine         │   │ Producer       │   │ Status Management  │   │
│  │                │   │                │   │                    │   │
│  └────────────────┘   └────────────────┘   └────────────────────┘   │
│                                                                      │
│                          Centralized Configuration                   │
│                      (shared/config/settings.py)                     │
│                                                                      │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
                       ┌───────────────┴────────────────┐
                       │                                │
                       ▼                                ▼
┌──────────────────────────────────┐  ┌─────────────────────────────┐
│                                  │  │                             │
│        Matching Service          │  │     External Systems        │
│  (Handles all bundle logic)      │  │  - SMTP Server             │
│                                  │  │  - Kafka Event Bus         │
│                                  │  │  - Database                │
└──────────────────────────────────┘  └─────────────────────────────┘
```

### Architectural Changes

#### What Was Removed
1. **Email Batching System**: All batch logic moved to Matching Service
2. **Phone Call Batching**: Bundle composition handled by Matching Service
3. **Placement Request Tracking**: Replaced by bundle system in Matching Service
4. **Complex Template Selection**: Simplified to basic templates

#### New Simplified Flow
1. Matching Service creates bundles (Therapeutenanfrage)
2. Matching Service calls Communication Service API to create email/call
3. Communication Service sends email or schedules call
4. Communication Service publishes completion events
5. Matching Service handles all response processing

## Email System (Simplified)

### Description
The Email System now focuses solely on sending individual emails and tracking their status. Bundle composition and patient grouping is handled entirely by the Matching Service.

### Key Components

#### 1. Email Manager
- **Purpose**: Creates and stores email records
- **Functions**:
  - Accepts email creation requests via API
  - Validates email data
  - Stores emails in database
  - Publishes creation events

#### 2. Email Queue Manager
- **Purpose**: Processes queued emails for sending
- **Functions**:
  - Fetches QUEUED emails from database
  - Sends via SMTP
  - Updates status (SENT/FAILED)
  - Publishes sent events

#### 3. Template Engine
- **Purpose**: Renders email templates
- **Functions**:
  - Loads Jinja2 templates
  - Populates with provided data
  - Generates HTML and text versions

### Database Schema (Simplified)
```sql
-- Email tracking with German field names
CREATE TABLE communication_service.emails (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    betreff VARCHAR(255) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT NOT NULL,
    empfaenger_email VARCHAR(255) NOT NULL,
    empfaenger_name VARCHAR(255) NOT NULL,
    absender_email VARCHAR(255) NOT NULL,
    absender_name VARCHAR(255) NOT NULL,
    antwort_erhalten BOOLEAN DEFAULT FALSE,
    antwortdatum TIMESTAMP,
    antwortinhalt TEXT,
    nachverfolgung_erforderlich BOOLEAN DEFAULT FALSE,
    nachverfolgung_notizen TEXT,
    status emailstatus DEFAULT 'DRAFT',
    queued_at TIMESTAMP,
    sent_at TIMESTAMP,
    fehlermeldung TEXT,
    wiederholungsanzahl INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

Note: The `placement_request_ids` and `batch_id` columns have been removed. Bundle tracking is now handled by the Matching Service through the `therapeutenanfrage.email_id` foreign key.

## Phone Call Scheduling System

### Description
The Phone Call Scheduling System schedules and tracks phone calls to therapists, particularly for follow-ups when emails don't receive responses.

### Key Components

#### 1. Call Scheduler
- **Purpose**: Creates and manages phone call schedules
- **Functions**:
  - Schedules calls based on therapist availability
  - Finds next available time slot
  - Creates call records
  - Handles automatic follow-ups for unanswered emails

#### 2. Availability Parser
- **Purpose**: Interprets therapist availability data
- **Functions**:
  - Parses `telefonische_erreichbarkeit` JSON
  - Identifies available time slots
  - Checks for conflicts

#### 3. Status Tracker
- **Purpose**: Tracks call statuses and outcomes
- **Functions**:
  - Records call attempts
  - Updates call outcomes
  - Triggers follow-up actions

### Database Schema
```sql
-- Phone call tracking with German field names
CREATE TABLE communication_service.phone_calls (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    geplantes_datum DATE NOT NULL,
    geplante_zeit TIME NOT NULL,
    dauer_minuten INTEGER DEFAULT 5,
    tatsaechliches_datum DATE,
    tatsaechliche_zeit TIME,
    status VARCHAR(50) DEFAULT 'scheduled',
    ergebnis TEXT,
    notizen TEXT,
    wiederholen_nach DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

Note: The `phone_call_batches` table has been removed. Bundle references are now managed by the Matching Service.

## Integration with Matching Service

### API-Based Integration
The Communication Service now provides simple APIs that the Matching Service calls:

#### Email Creation
```
POST /api/emails
{
  "therapist_id": 123,
  "betreff": "Therapieanfrage für mehrere Patienten",
  "body_html": "<html>...</html>",
  "body_text": "...",
  "empfaenger_email": "therapist@example.com",
  "empfaenger_name": "Dr. Schmidt"
}
```

The Matching Service:
1. Creates the bundle (Therapeutenanfrage)
2. Calls this API to create the email
3. Stores the returned email_id in therapeutenanfrage.email_id

#### Phone Call Scheduling
```
POST /api/phone-calls
{
  "therapist_id": 123,
  "notizen": "Follow-up for bundle #456"
}
```

### Event-Based Updates
Communication Service publishes events that Matching Service consumes:
- `communication.email_sent`: Email successfully sent
- `communication.email_failed`: Email sending failed
- `communication.call_completed`: Phone call completed

## Therapist Availability Data Structure

The `telefonische_erreichbarkeit` field in the Therapist model uses a JSON structure to store availability:

```json
{
  "monday": [
    {"start": "09:00", "end": "12:00"},
    {"start": "14:00", "end": "16:30"}
  ],
  "wednesday": [
    {"start": "10:00", "end": "14:00"}
  ],
  "friday": [
    {"start": "08:30", "end": "11:30"}
  ]
}
```

## Email Flow (Simplified)

### End-to-End Process

```
┌─────────────────────┐     ┌─────────────────────┐    ┌─────────────────────┐
│                     │     │                     │    │                     │
│ 1. Matching Service │────►│ 2. Email Creation   │───►│ 3. Sending          │
│                     │     │                     │    │                     │
│ - Creates bundle    │     │ - API call received │    │ - Fetch QUEUED      │
│ - Prepares content  │     │ - Validate data     │    │ - Use SMTP settings │
│ - Calls Email API   │     │ - Status: QUEUED    │    │ - Status: SENT      │
└─────────────────────┘     └─────────────────────┘    └──────────┬──────────┘
                                                                   │
                                                                   ▼
┌─────────────────────┐     ┌─────────────────────┐    ┌─────────────────────┐
│                     │     │                     │    │                     │
│ 6. Bundle Update    │◄────│ 5. Response Update  │◄───│ 4. Event Publishing │
│                     │     │                     │    │                     │
│ - Matching handles  │     │ - Manual update     │    │ - email.sent event  │
│ - Updates bundle    │     │ - Via API call      │    │ - Consumed by Match │
│ - Cooling period    │     │ - Response tracking │    │ - Status updates    │
└─────────────────────┘     └─────────────────────┘    └─────────────────────┘
```

## Centralized Configuration and Settings

All service configuration is centralized in `shared/config/settings.py`:

### Configuration Access

```python
from shared.config import get_config

config = get_config()

# Get SMTP settings
smtp_settings = config.get_smtp_settings()

# Get service URLs
matching_url = config.get_service_url("matching", internal=True)
```

### Environment-Based Configuration

The service supports multiple environments:

1. **Development** (default):
   - Debug mode enabled
   - Local SMTP server (port 1025)
   - Verbose logging

2. **Production**:
   - Debug mode disabled
   - Real SMTP server with TLS
   - Secure defaults enforced

3. **Testing**:
   - Separate test configuration
   - Mock SMTP server
   - Isolated test database

## Resilience Patterns

### Robust Kafka Producer

The service uses the shared RobustKafkaProducer with automatic configuration:

```python
from shared.kafka.robust_producer import RobustKafkaProducer

# Configuration loaded automatically from shared.config
producer = RobustKafkaProducer(service_name="communication-service")
```

### SMTP Error Handling

Email sending includes comprehensive error handling:
- Connection failures are logged
- Failed emails are marked with status
- Retry logic for transient failures
- Graceful degradation

## REST API Endpoints

The Communication Service exposes these simplified API endpoints:

### Email Endpoints:
- `GET /api/emails`: Get all emails (with optional filters)
- `POST /api/emails`: Create a new email
- `GET /api/emails/<id>`: Get a specific email
- `PUT /api/emails/<id>`: Update an email (including response tracking)

### Phone Call Endpoints:
- `GET /api/phone-calls`: Get all phone calls (with optional filters)
- `POST /api/phone-calls`: Create a new phone call (with automatic scheduling)
- `GET /api/phone-calls/<id>`: Get a specific phone call
- `PUT /api/phone-calls/<id>`: Update a phone call
- `DELETE /api/phone-calls/<id>`: Delete a phone call

Note: All batch-related endpoints have been removed.

## Best Practices

1. **Separation of Concerns**:
   - Communication Service only sends communications
   - Matching Service handles all bundle logic
   - Clear API boundaries between services

2. **Configuration Management**:
   - Always use `shared.config` for all settings
   - Never hardcode URLs, credentials, or settings
   - Use environment variables for deployment-specific values

3. **API Design**:
   - Simple, focused endpoints
   - Let Matching Service handle complexity
   - Return appropriate HTTP status codes

4. **Event Processing**:
   - Publish events for significant actions
   - Keep event payloads minimal
   - Use consistent event schema

## Migration Notes

### What Changed
1. **Removed Components**:
   - Email batching system
   - Phone call batching system
   - Bundle composition logic
   - Complex template selection

2. **Simplified Responsibilities**:
   - Only send emails
   - Only schedule calls
   - Only track status
   - No bundle logic

3. **New Integration Pattern**:
   - API-driven from Matching Service
   - Event-based status updates
   - Foreign key references in Matching Service

### Benefits of Simplification
1. **Clearer Architecture**: Each service has distinct responsibilities
2. **Easier Maintenance**: Less complex logic in Communication Service
3. **Better Scalability**: Services can scale independently
4. **Reduced Coupling**: Services communicate through well-defined APIs