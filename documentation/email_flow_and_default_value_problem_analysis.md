# Email Flow and Default Value Problem Analysis

## The Default Value Problem

### Problem Description
The Communication Service has an issue with default values for `sender_email` and `sender_name` not being properly applied during email creation. When creating emails through the API endpoint at `/api/emails`, and these fields are omitted from the request, the database operation fails with a `NOT NULL` constraint violation. This happens despite the code appearing to set default values:

```python
# Original problematic code in api/emails.py
email = Email(
    # Other fields...
    sender_email=args.get('sender_email', 'therapieplatz@peterhaupt.de'),
    sender_name=args.get('sender_name', 'Boona Therapieplatz-Vermittlung'),
    # More fields...
)
```

### Root Causes Analysis
1. **Inconsistent Default Value Sources**:
   - The API endpoint in `api/emails.py` hard-coded default values
   - The `email_sender.py` utility pulled defaults from Flask app.config
   - No single source of truth for these critical values

2. **Default Value Application Issues**:
   - Flask-RESTful's `reqparse` might not be handling the defaults correctly
   - The values might be getting overridden or lost in the process

3. **NULL Handling for Collections**:
   - `placement_request_ids` field was at risk of being `None`, causing errors when treated as iterable

### Impact
- Users must always manually specify sender details in every API request
- Database constraint violations when these fields are missing
- Inconsistent sender information across different email creation paths
- Potential for `NoneType` errors when handling placement request IDs

## Complete Email Flow

```
┌─────────────────┐
│ Matching Service│
│                 │
│ Creates match   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Kafka Event Bus │
│                 │
│ match.created   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Communication   │
│ Service         │
│ (Event Consumer)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐      ┌────────────────┐
│ Email Creation & Storage            │      │ Database       │
│                                     │─────>│                │
│ **ISSUE: Default Values Applied**   │      │ - Email        │
│ (API: hardcoded defaults in code)   │      │ - EmailBatch   │
└────────┬────────────────────────────┘      └────────────────┘
         │
         ▼
┌─────────────────┐
│ Kafka Event Bus │
│                 │
│ email.created   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Email Batch Processing              │
│                                     │
│ **Uses get_smtp_settings()**        │
│ (gets defaults from app.config)     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Email Queue     │
│                 │
│ (QUEUED status) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐      ┌────────────────┐
│ Email Sending Process               │      │ SMTP Server    │
│                                     │─────>│                │
│ **Uses get_smtp_settings()**        │      │                │
│ (for SMTP connection credentials)   │      │                │
└────────┬────────────────────────────┘      └────────────────┘
         │
         ▼
┌─────────────────┐
│ Email Status    │
│ Update          │
│ (SENT status)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Kafka Event Bus │
│                 │
│ email.sent      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Unanswered      │
│ Email Check     │
│ (after 7 days)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Phone Call      │
│ Scheduler       │
│                 │
└─────────────────┘
```

## Detailed Email Process Flow

### 1. Email Creation
- **Trigger**: Via API call or internal process (like batch creation)
- **Process**: 
  1. Parse request arguments or gather data internally
  2. Apply default values for missing fields (where the issue occurs)
  3. Create Email database entity
  4. Create associated EmailBatch records
- **Status**: Set to DRAFT initially
- **Event**: Publishes `email.created` event to Kafka

### 2. Email Batching
- **Trigger**: Daily scheduled process (1 AM)
- **Process**:
  1. Group placement requests by therapist
  2. Apply 7-day contact frequency rule
  3. Generate appropriate email content based on count
  4. Move emails to QUEUED status
- **Status**: Changes to QUEUED
- **Configuration**: Uses `get_smtp_settings()` for sender information

### 3. Email Sending
- **Trigger**: Periodic queued email processing
- **Process**:
  1. Query for emails with QUEUED status
  2. Set status to SENDING
  3. Create MIME message with HTML and plain text
  4. Connect to SMTP server and send
  5. Update status to SENT or FAILED
- **Status**: Changes to SENDING then SENT/FAILED
- **Event**: Publishes `email.sent` event on success

### 4. Response Tracking
- **Trigger**: Manual input or future automated system
- **Process**:
  1. Record response status and date
  2. Process any feedback from therapist
- **Status**: No status change, but `response_received` flag updated

### 5. Follow-up Processing
- **Trigger**: Daily check for unanswered emails (7 days old)
- **Process**:
  1. Identify emails sent 7+ days ago without response
  2. Schedule follow-up phone calls automatically
- **Action**: Creates PhoneCall records for follow-up

## Configuration and Fixes Implemented

### 1. Centralized Configuration (`config.py`)
Created a central configuration file that:
- Defines all configuration parameters in one place
- Supports environment variable overrides
- Provides sensible defaults
- Makes configuration changes easy and consistent

```python
# New centralized config.py
SMTP_HOST = os.environ.get("SMTP_HOST", "127.0.0.1")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "therapieplatz@peterhaupt.de")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "***REMOVED_EXPOSED_PASSWORD***")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "True").lower() == "true"

# Email sender defaults
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "therapieplatz@peterhaupt.de")
EMAIL_SENDER_NAME = os.environ.get("EMAIL_SENDER_NAME", "Boona Therapieplatz-Vermittlung")
```

### 2. Flask App Configuration (`app.py`)
Modified to use the centralized config:
```python
# Configure email settings from config file
app.config["SMTP_HOST"] = config.SMTP_HOST
app.config["SMTP_PORT"] = config.SMTP_PORT
app.config["SMTP_USERNAME"] = config.SMTP_USERNAME
app.config["SMTP_PASSWORD"] = config.SMTP_PASSWORD
app.config["SMTP_USE_TLS"] = config.SMTP_USE_TLS
app.config["EMAIL_SENDER"] = config.EMAIL_SENDER
app.config["EMAIL_SENDER_NAME"] = config.EMAIL_SENDER_NAME
```

### 3. SMTP Settings Function (`email_sender.py`)
Enhanced to use config consistently:
```python
def get_smtp_settings():
    """Get SMTP settings from app config or use defaults."""
    try:
        # Try to get settings from Flask app config
        return {
            'sender': current_app.config.get('EMAIL_SENDER', config.EMAIL_SENDER),
            'sender_name': current_app.config.get('EMAIL_SENDER_NAME', config.EMAIL_SENDER_NAME),
            # Other settings...
        }
    except RuntimeError:
        # Not in Flask app context, use defaults from config file
        return {
            'sender': config.EMAIL_SENDER,
            'sender_name': config.EMAIL_SENDER_NAME,
            # Other settings...
        }
```

### 4. Email API Endpoint (`emails.py`)
Modified to use consistent defaults:
```python
# Get email settings from centralized configuration
smtp_settings = get_smtp_settings()

# Create new email with proper defaults
email = Email(
    # Required fields...
    sender_email=args.get('sender_email', smtp_settings['sender']),
    sender_name=args.get('sender_name', smtp_settings['sender_name']),
    placement_request_ids=args.get('placement_request_ids', []),  # Empty list default
    # Other fields...
)
```

## Next Steps for Troubleshooting

1. **Verify Database Schema**:
   - Ensure the Email table schema requires NOT NULL for sender fields
   - Check for any default constraints at the database level

2. **Test API Endpoint**:
   - Test with explicit sender values first
   - Test with omitted sender values and observe behavior
   - Add explicit logging of the values before database operation

3. **Debug Database Operation**:
   - Add logging to show the exact SQL being generated
   - Trace the values through the SQLAlchemy object lifecycle

4. **Monitor SQLAlchemy Session**:
   - Check if any middleware or hooks are modifying the session
   - Verify that flush and commit operations work as expected

5. **Implement Sanitization Middleware**:
   - Consider adding pre-save hooks to enforce defaults
   - Add validation to catch missing values before database errors

## Test Cases to Verify Fix

1. **Direct API Test**:
   ```bash
   # Without sender fields - should use defaults
   curl -X POST http://localhost:8004/api/emails \
     -H "Content-Type: application/json" \
     -d '{
       "therapist_id": 1,
       "subject": "Test Subject",
       "body_html": "<p>Test Body</p>",
       "recipient_email": "test@example.com",
       "recipient_name": "Test Recipient",
       "placement_request_ids": []
     }'
   ```

2. **Batch Email Creation Test**:
   - Trigger the batch email creation process
   - Verify emails are created with correct sender details

3. **Email Sending Test**:
   - Move emails to QUEUED status
   - Trigger the send process
   - Verify SMTP connection details are correct