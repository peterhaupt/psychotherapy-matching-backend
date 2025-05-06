# Communication Service Architecture

## Overview

The Communication Service is responsible for managing all interaction with therapists, including email communication and phone call scheduling. This document describes the architecture of the service, with specific focus on the email batching system and phone call scheduling components.

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
│  │ Template       │   │ SMTP Client    │   │ Call Tracking &    │    │
│  │ Engine         │   │                │   │ Status Management  │    │
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

### Data Flow

1. **Placement Request Created**:
   - Matching Service creates a placement request
   - Publishes a `match.created` event to Kafka

2. **Request Processing**:
   - Communication Service receives the event
   - Checks if therapist has been contacted in the last 7 days
   - If yes: Adds request to therapist's waiting batch
   - If no: Adds request to therapist's ready-to-send batch

3. **Batch Processing**:
   - Daily job processes all ready-to-send batches
   - Generates one email per therapist with all patients
   - Updates therapist's last contact date

4. **Email Dispatch**:
   - Queues emails for sending via SMTP
   - Tracks send status
   - Handles retry logic for failed sends

### Database Schema
The email batching system relies on these key tables:
- `emails`: Tracks all emails sent to therapists
- `email_batches`: Groups multiple placement requests into a single email
- `email_queue`: Manages scheduled emails pending delivery

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
- `call_batches`: Groups multiple placement requests into a single call
- `call_history`: Maintains a record of all call attempts and outcomes

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

This structure allows for:
- Multiple days of availability
- Multiple time slots per day
- Precise start and end times

## Integration with Other Services

### Matching Service Integration
- Receives `match.created` events for new placement requests
- Subscribes to `match.status_changed` events to track changes
- Publishes `communication.email_sent` events when emails are sent
- Publishes `communication.call_scheduled` events when calls are scheduled

### Patient Service Integration
- Retrieves patient details for communication content
- Tracks patient status updates based on communication outcomes

### Therapist Service Integration
- Retrieves therapist details and availability information
- Receives updates about therapist status changes
- Updates therapist contact history

## Implementation Approach

### Phase 1: Email Batching System
1. Update Therapist model with new fields
2. Create database schema for email batching
3. Implement batch grouping algorithm
4. Create frequency limitation logic
5. Develop template integration

### Phase 2: Phone Call Scheduling
1. Create phone call table structure
2. Implement availability slot parser
3. Develop scheduling algorithm
4. Create rescheduling logic
5. Implement prioritization based on potential availability

### Phase 3: Integration
1. Connect with Matching Service events
2. Implement automated scheduling
3. Create status update mechanisms
4. Add reporting capabilities