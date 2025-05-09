# Communication Service

## Summary
This document details the implementation of the Communication Service for the Psychotherapy Matching Platform. The service handles all communication-related operations including email management, phone call scheduling, template rendering, and message dispatching. It provides a foundation for both automated and manual communication with therapists.

## Current Status
The Communication Service has been implemented with these components:

- **Email Model**: Database storage for emails with status tracking and response monitoring
- **Email Batch System**: Complete implementation of email batching for grouping multiple patient requests
- **Phone Call System**: Complete implementation of phone call scheduling and management
- **API Endpoints**: REST endpoints for email and phone call operations
- **Kafka Integration**: Robust event producers and consumers with resilience features
- **Email Sending Functionality**: Integrated SMTP client for email delivery
- **Template System**: Enhanced Jinja2-based HTML template system

## Models Implementation

### Email Model
The Email model in `communication_service/models/email.py` stores all information related to emails, including:
- Email metadata (sender, recipient, subject)
- Body content in HTML and plain text formats
- Response tracking fields
- Status information and timestamps

### Email Batch Model
The Email Batch model in `communication_service/models/email_batch.py` establishes the relationship between emails and placement requests, supporting the batching of multiple requests into a single email.

### Phone Call Models
Two models handle phone call scheduling and batch processing:
- `PhoneCall` model: Stores scheduling information, outcomes, and status
- `PhoneCallBatch` model: Tracks which placement requests are discussed in each call

## API Implementation

### API Endpoints

#### Email Endpoints:
- **EmailResource**: Operations on individual emails (GET, PUT)
- **EmailListResource**: Collection operations (GET, POST)
- **EmailResponseResource**: Operations for tracking email responses (GET, POST)
- **EmailBatchListResource**: Operations for managing batches for a specific email (GET, POST)
- **EmailBatchResource**: Operations on individual email batches (GET, PUT, DELETE)

#### Phone Call Endpoints:
- **PhoneCallResource**: Operations on individual phone calls (GET, PUT, DELETE)
- **PhoneCallListResource**: Collection operations (GET, POST)
- **PhoneCallBatchResource**: Operations on phone call batches (GET, PUT)

## Email Batching System

The email batching system provides a sophisticated way to group multiple patient requests into a single email to therapists.

### Key Features:
- **Frequency Limitation**: Enforces maximum one email per therapist per week
- **Patient Grouping**: Groups multiple patients for a therapist into a single email
- **Dynamic Templating**: Selects appropriate templates based on batch size
- **Batch Tracking**: Tracks the included placement requests in each email
- **Response Management**: Records responses at both email and individual batch level
- **Prioritization**: Orders patients by registration date for batching

### Implementation
Key components are found in `communication_service/utils/email_sender.py`:
- `can_contact_therapist()`: Enforces the 7-day frequency limitation
- `create_batch_email()`: Creates emails with multiple patient requests
- `process_pending_requests()`: Identifies requests that need to be batched
- `send_queued_emails()`: Processes the email queue with batch awareness

## Phone Call Scheduling System

The phone call scheduling system provides automated scheduling of calls based on therapist availability:

### Key Features:
- **Availability Parsing**: Converts therapist's JSON availability data into usable time slots
- **Slot Finding**: Locates appropriate time slots for scheduling calls
- **Follow-up Automation**: Automatically schedules follow-up calls for unanswered emails after 7 days
- **Batch Processing**: Handles multiple placement requests in a single call
- **5-Minute Intervals**: Schedules calls in 5-minute time blocks

### Implementation
Key components are in `communication_service/utils/phone_call_scheduler.py`:
- `find_available_slot()`: Finds the next available time slot for a therapist
- `is_slot_booked()`: Checks if a time slot is already booked
- `schedule_call_for_email()`: Schedules a call for an unanswered email
- `schedule_follow_up_calls()`: Processes all emails that need follow-up calls

## Email Template System

The service uses a structured template system with Jinja2 in `communication_service/templates/`:
- `base_email.html`: Base template with common structure
- `initial_contact.html`: Template for first contact with therapist
- `batch_request.html`: Template for multiple patient requests
- `follow_up.html`: Template for follow-up communications
- `confirmation.html`: Template for confirming accepted patients

## Resilient Kafka Integration

A robust Kafka producer handles connection issues and message persistence. Key features include:
- **Connection Retries**: Exponential backoff retry logic for connecting to Kafka
- **Message Persistence**: Local storage of messages when Kafka is unavailable
- **Background Processing**: Thread for sending queued messages when connection is restored
- **Error Handling**: Proper handling of various error conditions

## Event Handling

The service consumes matching events to track changes in placement requests:
- `handle_matching_event()`: Processes events from the matching service
- `process_email_queue()`: Regularly checks for emails that need to be sent
- `check_unanswered_emails()`: Identifies emails that need follow-up calls
- `schedule_daily_batch_processing()`: Runs the daily batch email processing