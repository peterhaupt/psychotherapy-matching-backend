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

## Email Flow Process

The Communication Service processes emails through these stages:

1. **Email Creation**
   - **Trigger**: Via API call or internal process (like batch creation)
   - **Process**:
     - Parse request arguments
     - Apply default values for missing fields with proper null handling
     - Create Email database entity and associated EmailBatch records
   - **Status**: Set to DRAFT initially
   - **Event**: Publishes `email.created` event

2. **Email Batching**
   - **Trigger**: Daily scheduled process (1 AM)
   - **Process**: 
     - Group placement requests by therapist
     - Apply 7-day contact frequency rule
     - Generate appropriate email content
   - **Status**: Changes to QUEUED

3. **Email Sending**
   - **Trigger**: Periodic queued email processing
   - **Process**:
     - Create MIME message with HTML and plain text
     - Connect to SMTP server and send
     - Update status to SENT or FAILED
   - **Event**: Publishes `email.sent` event on success

4. **Follow-up Processing**
   - **Trigger**: Daily check for unanswered emails (7 days old)
   - **Process**:
     - Schedule follow-up phone calls for unanswered emails
   - **Action**: Creates PhoneCall records for follow-up

## Centralized Configuration

The service uses a centralized configuration approach in `config.py`:
- **Environment Variables**: All settings can be overridden via environment
- **Default Values**: Sensible defaults for development
- **Application Settings**: Database, SMTP, and other service settings
- **Email Defaults**: Default sender information

The configuration is used consistently throughout the service:
- In the Flask app via `app.config`
- In the `get_smtp_settings()` utility function
- Directly in components when needed

## Previously Known Issues (Now Fixed)

### Default Value Handling in RequestParser ✓

**Issue**: When creating emails through the API, default values for `sender_email` and `sender_name` were not correctly applied when these fields were omitted from the request.

**Root Cause**: Flask-RESTful's RequestParser adds defined arguments to the result dictionary with a value of `None` when they're not provided in the request. The `.get(key, default)` method only uses its default value when the key doesn't exist in the dictionary, not when it exists with a value of `None`.

**Solution**: Modified the email creation code to use the Python `or` operator for default values:

```python
# Changed from this:
sender_email=args.get('sender_email', smtp_settings['sender'])

# To this:
sender_email=args.get('sender_email') or smtp_settings['sender']
```

This properly handles both missing keys and keys with `None` values.

### Placement Request IDs Handling ✓

**Issue**: The service failed to handle null `placement_request_ids` properly in email creation.

**Solution**: Updated the code to use the `or` operator for proper null handling:
```python
placement_request_ids=args.get('placement_request_ids') or []
```

## Future Enhancements

### Code Improvements
- Improve error handling and validation
- Refactor to use a service layer pattern

### Functional Enhancements
- Enhanced email response tracking
- Advanced batch prioritization
- Automated email content generation
- Integration with calendar systems for call scheduling