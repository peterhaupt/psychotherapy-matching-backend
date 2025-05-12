# Communication Service Architecture

## Overview

The Communication Service is responsible for managing all interaction with therapists, including email communication and phone call scheduling. This document describes the architecture of the service, with specific focus on the email batching system, phone call scheduling components, and resilience patterns.

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Communication Service                           │
│                                                                      │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐    │
│  │                │   │                │   │                    │    │
│  │ Email Batching │   │  Email Queue   │   │ Phone Call         │    │
│  │ System         │◄──┤  Manager       │◄──┤ Scheduling System  │    │
│  │                │   │                │   │                    │    │
│  └────────┬───────┘   └───────┬────────┘   └──────────┬─────────┘    │
│           │                   │                       │              │
│           ▼                   ▼                       ▼              │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐    │
│  │                │   │                │   │                    │    │
│  │ Template       │   │ Robust Kafka   │   │ Call Tracking &    │    │
│  │ Engine         │   │ Producer       │   │ Status Management  │    │
│  │                │   │                │   │                    │    │
│  └────────────────┘   └────────────────┘   └────────────────────┘    │
│                                                                      │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                          External Systems                            │
│                                                                      │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐    │
│  │                │   │                │   │                    │    │
│  │ SMTP Server    │   │ Kafka Event    │   │ Database           │    │
│  │                │   │ Bus            │   │                    │    │
│  └────────────────┘   └────────────────┘   └────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Email Batching System

### Description
The Email Batching System is responsible for grouping patients by therapist, enforcing contact frequency limits, and generating batch emails that include multiple patient requests.

### Key Components

#### 1. Batch Manager
- **Purpose**: Tracks and groups patient placement requests by therapist
- **Functions**:
  - Accepts new placement requests from the Matching Service
  - Groups requests by therapist ID
  - Enforces the 7-day contact frequency rule
  - Prioritizes patients based on registration date

#### 2. Email Composer
- **Purpose**: Creates email content from batched requests
- **Functions**:
  - Selects appropriate email template (initial contact, follow-up, etc.)
  - Populates template with patient information
  - Generates both HTML and plain text versions
  - Adds tracking information

#### 3. Scheduling Logic
- **Purpose**: Determines when emails should be sent
- **Functions**:
  - Checks each therapist's last contact date
  - Creates a queue of therapists eligible for contact
  - Schedules batch emails for immediate or future delivery

### Database Schema
The email batching system relies on these key tables:
- `emails`: Tracks all emails sent to therapists
- `email_batches`: Groups multiple placement requests into a single email

## Phone Call Scheduling System

### Description
The Phone Call Scheduling System automatically schedules phone calls to therapists when email communication hasn't received a response after 7 days.

### Key Components

#### 1. Call Scheduler
- **Purpose**: Creates and manages phone call schedules
- **Functions**:
  - Automatically schedules calls 7 days after unanswered emails
  - Parses therapist availability JSON for available time slots
  - Batches multiple patients into single calls
  - Prioritizes "potentially available" therapists
  - Schedules calls in 5-minute intervals

#### 2. Call Queue Manager
- **Purpose**: Manages the queue of scheduled calls
- **Functions**:
  - Provides daily call lists for staff
  - Tracks call outcomes
  - Handles rescheduling of failed calls
  - Enforces the 4-week cooling period after rejections

#### 3. Status Tracker
- **Purpose**: Tracks call statuses and outcomes
- **Functions**:
  - Records call attempt history
  - Logs call outcomes and notes
  - Updates placement request statuses
  - Triggers follow-up actions based on call results

### Implementation

The Phone Call Scheduling System has been fully implemented with these components:

1. **PhoneCall Model**: Stores information about scheduled and completed calls
2. **PhoneCallBatch Model**: Links calls to placement requests
3. **PhoneCallStatus Enum**: Defines possible call statuses (scheduled, completed, failed, canceled)
4. **Availability Parser**: Parses the therapist's JSON availability structure
5. **Slot Finder**: Identifies available time slots for scheduling
6. **Follow-up Scheduler**: Automatically schedules calls for unanswered emails

### Data Flow

1. **Initial Trigger**:
   - Daily job checks for unanswered emails older than 7 days
   - Creates call scheduling tasks for each therapist

2. **Schedule Generation**:
   - System parses therapist's `telefonische_erreichbarkeit` JSON
   - Identifies available time slots
   - Assigns calls to slots based on priority
   - Creates call entries in the database

3. **Call Execution**:
   - Staff views scheduled calls in the system
   - Makes calls during scheduled times
   - Records outcomes (success, failed, rescheduled)

4. **Result Processing**:
   - System processes call outcomes
   - Updates placement request statuses
   - Reschedules failed calls
   - Applies 4-week cooling period for rejected requests

### Database Schema
The phone call system relies on these key tables:
- `phone_calls`: Tracks all scheduled and completed calls
- `phone_call_batches`: Groups multiple placement requests into a single call

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

## Email Flow

### End-to-End Process

The email communication process follows this flow:

```
┌────────────────────────┐     ┌────────────────────────┐    ┌────────────────────────┐
│                        │     │                        │    │                        │
│ 1. Creation            │────►│ 2. Batching            │───►│ 3. Sending             │
│                        │     │                        │    │                        │
│ - API or batch process │     │ - Group by therapist   │    │ - Fetch QUEUED emails  │
│ - Default handling     │     │ - 7-day frequency rule │    │ - SMTP connection      │
│ - Status: DRAFT        │     │ - Status: QUEUED       │    │ - Status: SENT/FAILED  │
└────────────────────────┘     └────────────────────────┘    └──────────┬─────────────┘
                                                                         │
                                                                         ▼
┌────────────────────────┐     ┌────────────────────────┐    ┌────────────────────────┐
│                        │     │                        │    │                        │
│ 6. Phone Call          │◄────│ 5. Response Tracking   │◄───│ 4. Event Publishing    │
│                        │     │                        │    │                        │
│ - Schedule calls       │     │ - Manual input         │    │ - email.sent event     │
│ - 7-day followup       │     │ - Update response flag │    │ - Event consumers      │
│ - Batch calls          │     │ - Process feedback     │    │ - Matching updates     │
└────────────────────────┘     └────────────────────────┘    └────────────────────────┘
```

### Configuration and Settings

The service uses a centralized configuration approach for all email-related settings:

1. **Configuration File (`config.py`)**:
   - Defines all settings with environment variable overrides
   - Default SMTP settings
   - Default sender information
   - Application-level settings

2. **Flask App Configuration**:
   - Loads settings from config.py
   - Makes them available via `current_app.config`

3. **Utility Functions**:
   - `get_smtp_settings()` provides consistent access to settings
   - Handles both in-app and out-of-app contexts

### Default Value Handling

The service implements proper handling of default values in the API:

- **RequestParser Behavior**: Flask-RESTful's RequestParser adds defined arguments to the result dictionary with value `None` when they're not in the request
- **Solution**: Use `or` operator for NULL handling: `args.get('sender_email') or smtp_settings['sender']`
- **Collections**: Handle NULL for collection fields: `args.get('placement_request_ids') or []`

This approach ensures that proper defaults are always applied, preventing NULL values from reaching the database.

## Resilience Patterns

### Robust Kafka Producer

A resilient Kafka producer was implemented to handle connection failures and ensure message delivery:

#### 1. Connection Resilience
- **Purpose**: Maintain reliable connection to Kafka
- **Functions**:
  - Exponential backoff retries for Kafka connection
  - Graceful handling of broker unavailability
  - Configurable timeout and retry parameters

#### 2. Message Persistence
- **Purpose**: Ensure no messages are lost during outages
- **Functions**:
  - In-memory queue for temporary outages
  - At-least-once delivery semantics
  - Message persistency

#### 3. Background Processing
- **Purpose**: Deliver messages without blocking application
- **Functions**:
  - Dedicated thread for message delivery
  - Automatic retry of failed deliveries
  - Priority-based message processing

This robust messaging implementation ensures that:
- The service can start even if Kafka is temporarily down
- Messages are never lost if Kafka becomes unavailable
- Failed messages are automatically retried
- The service is resilient to network issues

## REST API Endpoints

The Communication Service exposes these API endpoints:

### Email Endpoints:
- `GET /api/emails`: Get all emails (with optional filters)
- `POST /api/emails`: Create a new email
- `GET /api/emails/<id>`: Get a specific email
- `PUT /api/emails/<id>`: Update an email (including response tracking)
- `GET /api/emails/<id>/batches`: Get all batches for a specific email
- `POST /api/emails/<id>/batches`: Add a placement request to an email batch
- `GET /api/email-batches/<id>`: Get a specific email batch
- `PUT /api/email-batches/<id>`: Update a specific email batch
- `DELETE /api/email-batches/<id>`: Delete a specific email batch

### Phone Call Endpoints:
- `GET /api/phone-calls`: Get all phone calls (with optional filters)
- `POST /api/phone-calls`: Create a new phone call (with automatic scheduling)
- `GET /api/phone-calls/<id>`: Get a specific phone call
- `PUT /api/phone-calls/<id>`: Update a phone call
- `DELETE /api/phone-calls/<id>`: Delete a phone call
- `GET /api/phone-call-batches/<id>`: Get a specific phone call batch
- `PUT /api/phone-call-batches/<id>`: Update a phone call batch

## Integration with Other Services

### Matching Service Integration
- Receives `match.created` events for new placement requests
- Subscribes to `match.status_changed` events to track changes
- Publishes `communication.email_sent` events when emails are sent
- Publishes `communication.call_scheduled` events when calls are scheduled

### Therapist Service Integration
- Retrieves therapist details and availability information
- Uses the `potentially_available` flag for prioritization
- Accesses the `telefonische_erreichbarkeit` JSON structure for scheduling

## Best Practices

1. **Configuration Management**:
   - Use centralized configuration with environment overrides
   - Apply consistent default handling throughout the codebase
   - Document all configuration parameters

2. **API Implementation**:
   - Follow RESTful design principles
   - Implement proper validation
   - Handle NULL values explicitly using `or` operator
   - Return appropriate HTTP status codes

3. **Database Operations**:
   - Use proper session management
   - Implement comprehensive error handling
   - Roll back transactions on error
   - Use appropriate indexes

4. **Event Processing**:
   - Use the RobustKafkaProducer for resilience
   - Implement idempotent event handlers
   - Use consistent event schema
   - Process events asynchronously

## Future Improvements

1. **Code Refactoring**:
   - Add comprehensive error handling
   - Implement service layer pattern
   - Improve code organization and documentation

2. **Feature Enhancements**:
   - Enhanced response tracking
   - Advanced template customization
   - Improved batch prioritization
   - Better integration with calendar systems
   - Intelligent call time selection based on success rates