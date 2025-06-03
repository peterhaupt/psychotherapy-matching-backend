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
- **Centralized Configuration**: All settings managed through shared configuration

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

## Centralized Configuration

All Communication Service settings are managed through `shared/config/settings.py`:

```python
from shared.config import get_config

config = get_config()

# SMTP settings
smtp_settings = config.get_smtp_settings()
# Returns dict with: host, port, username, password, use_tls, sender, sender_name
```

### Environment Variables
Email/SMTP settings in `.env`:
- `SMTP_HOST`: SMTP server hostname (default: localhost)
- `SMTP_PORT`: SMTP server port (default: 1025 for development)
- `SMTP_USERNAME`: SMTP authentication username
- `SMTP_PASSWORD`: SMTP authentication password
- `SMTP_USE_TLS`: Enable TLS encryption (default: false)
- `EMAIL_SENDER`: Default sender email address
- `EMAIL_SENDER_NAME`: Default sender name

### Configuration Usage
The service uses configuration in multiple ways:

1. **Flask App Configuration** (in `app.py`):
```python
config = get_config()
smtp_settings = config.get_smtp_settings()
app.config["SMTP_HOST"] = smtp_settings["host"]
app.config["SMTP_PORT"] = smtp_settings["port"]
# ... etc
```

2. **Email Sending Utilities**:
```python
def get_smtp_settings():
    """Get SMTP settings from app config or use defaults."""
    try:
        # Try Flask app context first
        return {
            'host': current_app.config.get('SMTP_HOST', config.SMTP_HOST),
            # ... etc
        }
    except RuntimeError:
        # Fall back to centralized config
        return config.get_smtp_settings()
```

## Resilient Kafka Integration

The service uses the shared RobustKafkaProducer with centralized configuration:

```python
from shared.kafka.robust_producer import RobustKafkaProducer

# Automatically uses configuration from shared.config
producer = RobustKafkaProducer(service_name="communication-service")
```

Key features:
- Connection configuration loaded automatically
- Message persistence during Kafka outages
- Automatic reconnection with exponential backoff
- Background message queue processing

## Event Handling

The service consumes and produces events using centralized Kafka configuration:

### Consumed Events:
- `handle_matching_event()`: Processes events from the matching service
- `process_email_queue()`: Regularly checks for emails that need to be sent
- `check_unanswered_emails()`: Identifies emails that need follow-up calls
- `schedule_daily_batch_processing()`: Runs the daily batch email processing

### Published Events:
- `communication.email_created`: When a new email is created
- `communication.email_sent`: When an email is successfully sent
- `communication.call_scheduled`: When a phone call is scheduled
- `communication.call_completed`: When a phone call is completed

## Email Flow Process

The Communication Service processes emails through these stages:

1. **Email Creation**
   - Parse request arguments
   - Apply default values from centralized config
   - Create Email and EmailBatch records
   - Publish `email.created` event

2. **Email Batching**
   - Daily scheduled process (1 AM)
   - Group placement requests by therapist
   - Apply 7-day contact frequency rule
   - Generate appropriate email content

3. **Email Sending**
   - Use SMTP settings from centralized config
   - Create MIME message with HTML and plain text
   - Connect to SMTP server and send
   - Update status and publish events

4. **Follow-up Processing**
   - Daily check for unanswered emails (7 days old)
   - Schedule follow-up phone calls automatically

## Testing Email Functionality

For local development, you can use a mail catcher:

```bash
# Using MailHog (recommended)
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or using Python's built-in SMTP debugging server
python -m smtpd -n -c DebuggingServer localhost:1025
```

Then set in your `.env`:
```
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
```

## Best Practices

1. **Use Centralized Configuration**: Always use `shared.config` for settings
2. **Environment Variables**: Never hardcode SMTP credentials
3. **Default Value Handling**: Use the `or` operator for proper null handling
4. **Error Handling**: Implement proper SMTP error handling
5. **Testing**: Use mail catchers for local development
6. **Templates**: Keep email templates simple and responsive

## Previously Known Issues (Now Fixed)

### Default Value Handling in RequestParser ✓

**Issue**: Flask-RESTful's RequestParser adds `None` for undefined arguments, preventing `.get()` defaults from working.

**Solution**: Use the `or` operator:
```python
sender_email = args.get('sender_email') or smtp_settings['sender']
```

### Placement Request IDs Handling ✓

**Issue**: Null `placement_request_ids` not handled properly.

**Solution**: Use the `or` operator:
```python
placement_request_ids = args.get('placement_request_ids') or []
```

## Future Enhancements

### Code Improvements
- Service layer pattern implementation
- Enhanced validation middleware
- Async email sending

### Functional Enhancements
- Email open/click tracking
- Advanced template customization
- SMS notification support
- Calendar integration for scheduling
- Real-time communication dashboard