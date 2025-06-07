# Communication Service

## Summary
This document details the implementation of the Communication Service for the Psychotherapy Matching Platform. The service handles all communication-related operations including email management, phone call scheduling, template rendering, and message dispatching. The service has been simplified to focus solely on sending communications, with bundle logic moved to the Matching Service. All models and APIs now use German field names.

## Current Status ✅ FULLY UPDATED
The Communication Service has been fully updated with these components:

- **Email Model**: Database storage for emails with German field names
- **Phone Call System**: Complete implementation with German field names
- **API Endpoints**: REST endpoints accepting and returning German field names
- **Kafka Integration**: Robust event producers and consumers with resilience features
- **Email Sending Functionality**: Integrated SMTP client for email delivery
- **Template System**: Enhanced Jinja2-based HTML template system
- **Centralized Configuration**: All settings managed through shared configuration

### Recent Architectural Changes
- ❌ **Email Batch System**: REMOVED - Bundle logic moved to Matching Service
- ❌ **Phone Call Batch System**: REMOVED - Bundle logic moved to Matching Service
- ✅ **Simplified Design**: Communication Service now only sends emails and schedules calls
- ✅ **German Field Names**: All models and APIs now use German field names

## Models Implementation

### Email Model ✅ UPDATED
The Email model in `communication_service/models/email.py` stores all information related to emails with German field names:

```python
class Email(Base):
    # German field names matching database
    betreff = Column(String(255), nullable=False)  # subject
    empfaenger_email = Column(String(255), nullable=False)  # recipient_email
    empfaenger_name = Column(String(255), nullable=False)  # recipient_name
    absender_email = Column(String(255), nullable=False)  # sender_email
    absender_name = Column(String(255), nullable=False)  # sender_name
    antwort_erhalten = Column(Boolean, default=False)  # response_received
    antwortdatum = Column(DateTime)  # response_date
    antwortinhalt = Column(Text)  # response_content
    nachverfolgung_erforderlich = Column(Boolean, default=False)  # follow_up_required
    nachverfolgung_notizen = Column(Text)  # follow_up_notes
    fehlermeldung = Column(Text)  # error_message
    wiederholungsanzahl = Column(Integer, default=0)  # retry_count
```

### Phone Call Model ✅ UPDATED
The Phone Call model stores scheduling information with German field names:

```python
class PhoneCall(Base):
    # German field names matching database
    geplantes_datum = Column(Date, nullable=False)  # scheduled_date
    geplante_zeit = Column(Time, nullable=False)  # scheduled_time
    dauer_minuten = Column(Integer, default=5)  # duration_minutes
    tatsaechliches_datum = Column(Date)  # actual_date
    tatsaechliche_zeit = Column(Time)  # actual_time
    ergebnis = Column(Text)  # outcome
    notizen = Column(Text)  # notes
    wiederholen_nach = Column(Date)  # retry_after
```

### Removed Models ✅
- ❌ **EmailBatch**: Removed (bundle logic moved to Matching Service)
- ❌ **PhoneCallBatch**: Removed (bundle logic moved to Matching Service)

## API Implementation

### API Endpoints (German Field Names)

#### Email Endpoints:
- **EmailResource**: Operations on individual emails (GET, PUT)
- **EmailListResource**: Collection operations (GET, POST)

#### Phone Call Endpoints:
- **PhoneCallResource**: Operations on individual phone calls (GET, PUT, DELETE)
- **PhoneCallListResource**: Collection operations (GET, POST)

### Example API Usage

#### Create Email (POST /api/emails)
```json
{
  "therapist_id": 1,
  "betreff": "Therapieanfrage für mehrere Patienten",
  "body_html": "<html>...</html>",
  "body_text": "...",
  "empfaenger_email": "therapist@example.com",
  "empfaenger_name": "Dr. Schmidt"
}
```

#### Create Phone Call (POST /api/phone-calls)
```json
{
  "therapist_id": 1,
  "geplantes_datum": "2025-06-10",
  "geplante_zeit": "14:30",
  "dauer_minuten": 5
}
```

## Simplified Architecture

The Communication Service no longer handles bundle/batch logic. Instead:

1. **Matching Service** creates bundles and determines which patients to include
2. **Matching Service** calls Communication Service API to create emails/calls
3. **Communication Service** sends emails and schedules calls
4. **Communication Service** publishes events when emails are sent or calls completed
5. **Matching Service** handles responses and updates bundle status

### Key Simplifications:
- No more email batching logic
- No more placement request tracking
- No complex template selection based on batch size
- Clear separation of concerns

## Phone Call Scheduling System

The phone call scheduling system provides automated scheduling of calls based on therapist availability:

### Key Features:
- **Availability Parsing**: Converts therapist's JSON availability data into usable time slots
- **Slot Finding**: Locates appropriate time slots for scheduling calls
- **Follow-up Automation**: Automatically schedules follow-up calls for unanswered emails after 7 days
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
- `batch_request.html`: Template for multiple patient requests (legacy)
- `follow_up.html`: Template for follow-up communications
- `confirmation.html`: Template for confirming accepted patients

Note: Templates may need updating to work with the new bundle system.

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

## Resilient Kafka Integration

The service uses the shared RobustKafkaProducer with centralized configuration:

```python
from shared.kafka.robust_producer import RobustKafkaProducer

# Automatically uses configuration from shared.config
producer = RobustKafkaProducer(service_name="communication-service")
```

## Event Handling

The service consumes and produces events using centralized Kafka configuration:

### Consumed Events:
- `communication.send_email`: Request to send an email
- `communication.schedule_call`: Request to schedule a phone call

### Published Events:
- `communication.email_created`: When a new email is created
- `communication.email_sent`: When an email is successfully sent
- `communication.call_scheduled`: When a phone call is scheduled
- `communication.call_completed`: When a phone call is completed

## Email Flow Process

The simplified Communication Service processes emails through these stages:

1. **Email Creation** (via API from Matching Service)
   - Parse request arguments with German field names
   - Apply default values from centralized config
   - Create Email record
   - Publish `email.created` event

2. **Email Sending**
   - Use SMTP settings from centralized config
   - Create MIME message with HTML and plain text
   - Connect to SMTP server and send
   - Update status and publish events

3. **Response Tracking**
   - Manual update via API when response received
   - Matching Service handles bundle response logic

4. **Follow-up Processing**
   - Check for unanswered emails (7 days old)
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
7. **German Field Names**: Always use German field names in API requests and responses

## Migration Completed ✅

### From Batch System to Simple Communication

1. **Database**: Batch tables have been removed via migration
2. **Models**: EmailBatch and PhoneCallBatch classes removed
3. **API**: Batch-related endpoints removed
4. **Logic**: Bundle logic now resides in Matching Service

### Integration with New Bundle System

The Matching Service now:
1. Creates bundles (Therapeutenanfrage)
2. Calls Communication Service API to create email
3. Stores email_id in Therapeutenanfrage record
4. Handles all response processing and bundle updates

## Future Enhancements

### Functional Enhancements
- Email open/click tracking
- Advanced template customization
- SMS notification support
- Calendar integration for scheduling
- Real-time communication dashboard

## Current API Examples

### Email Operations

#### Get Email by ID
```bash
curl http://localhost:8004/api/emails/1
```

Response (with German fields):
```json
{
  "id": 1,
  "therapist_id": 123,
  "betreff": "Therapieanfrage",
  "empfaenger_email": "doctor@example.com",
  "empfaenger_name": "Dr. Schmidt",
  "absender_email": "noreply@example.com",
  "absender_name": "Therapy Platform",
  "status": "SENT",
  "antwort_erhalten": false,
  "antwortdatum": null,
  "sent_at": "2025-06-08T10:30:00"
}
```

#### Update Email Response
```bash
curl -X PUT http://localhost:8004/api/emails/1 \
  -H "Content-Type: application/json" \
  -d '{
    "antwort_erhalten": true,
    "antwortdatum": "2025-06-09T14:00:00",
    "antwortinhalt": "Ich kann 2 Patienten aufnehmen.",
    "nachverfolgung_erforderlich": false
  }'
```

### Phone Call Operations

#### Schedule Phone Call
```bash
curl -X POST http://localhost:8004/api/phone-calls \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "geplantes_datum": "2025-06-15",
    "geplante_zeit": "10:00",
    "dauer_minuten": 5,
    "notizen": "Follow-up für Bündel #45"
  }'
```

#### Update Call Outcome
```bash
curl -X PUT http://localhost:8004/api/phone-calls/1 \
  -H "Content-Type: application/json" \
  -d '{
    "tatsaechliches_datum": "2025-06-15",
    "tatsaechliche_zeit": "10:05",
    "status": "completed",
    "ergebnis": "Therapeut interessiert an 1 Patient",
    "notizen": "Will sich nächste Woche melden"
  }'
```