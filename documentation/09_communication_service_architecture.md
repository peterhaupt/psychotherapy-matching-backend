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
  - Disk-based storage for longer outages
  - Unique message IDs for tracking and de-duplication

#### 3. Background Processing
- **Purpose**: Deliver messages without blocking application
- **Functions**:
  - Dedicated thread for message delivery
  - Automatic retry of failed deliveries
  - Priority-based message processing

#### 4. Status Monitoring
- **Purpose**: Track message delivery status
- **Functions**:
  - Logging of send attempts and results
  - Status tracking for queued messages
  - Metrics for queue length and processing time

This robust messaging implementation ensures that:
- The service can start even if Kafka is temporarily down
- Messages are never lost if Kafka becomes unavailable
- Failed messages are automatically retried
- The service is resilient to network issues

## REST API Endpoints

The Communication Service exposes these API endpoints:

### Email Endpoints:
- `GET /api/emails`: Get all emails (with optional filters)
- `GET /api/emails/<id>`: Get a specific email
- `POST /api/emails`: Create a new email
- `PUT /api/emails/<id>`: Update an email

### Phone Call Endpoints:
- `GET /api/phone-calls`: Get all phone calls (with optional filters)
- `GET /api/phone-calls/<id>`: Get a specific phone call
- `POST /api/phone-calls`: Create a new phone call (with automatic scheduling)
- `PUT /api/phone-calls/<id>`: Update a phone call
- `DELETE /api/phone-calls/<id>`: Delete a phone call

### Phone Call Batch Endpoints:
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

## Future Enhancements

### Phase 1: Email Batching System Completion
1. Complete frequency limitation testing
2. Enhance batch grouping algorithm
3. Implement template selection logic

### Phase 2: Phone Call Scheduling Enhancements
1. Add advanced prioritization logic
2. Implement call outcome analytics
3. Add staff assignment features

### Phase 3: User Interface
1. Create dashboard for scheduled calls
2. Develop call result entry form
3. Implement calendar integration