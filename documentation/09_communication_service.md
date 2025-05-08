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

### Email Model (`communication_service/models/email.py`)

The Email model is built using SQLAlchemy and implements all required fields according to the specifications:

```python
class Email(Base):
    """Email database model."""

    __tablename__ = "emails"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Email metadata
    therapist_id = Column(Integer, nullable=False)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False)
    
    # Placement requests associated with this email (will be replaced by batches)
    placement_request_ids = Column(JSONB)
    
    # Batch identifier
    batch_id = Column(String(50))
    
    # Response tracking
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_content = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    
    # Status information
    status = Column(
        SQLAlchemyEnum(EmailStatus),
        default=EmailStatus.DRAFT
    )
    queued_at = Column(DateTime)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### Email Batch Model (`communication_service/models/email_batch.py`)

The newly implemented Email Batch model establishes the relationship between emails and placement requests, supporting the batching of multiple requests into a single email:

```python
class EmailBatch(Base):
    """Email batch database model.
    
    This model represents the relationship between emails and placement requests,
    allowing multiple placement requests to be grouped into a single email.
    """

    __tablename__ = "email_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    email_id = Column(
        Integer,
        ForeignKey("communication_service.emails.id", ondelete="CASCADE"),
        nullable=False
    )
    placement_request_id = Column(
        Integer,
        ForeignKey("matching_service.placement_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Batch metadata
    priority = Column(Integer, default=1)  # Higher numbers = higher priority
    included = Column(Boolean, default=True)  # Flag to indicate if the request was included in the email
    
    # Response tracking
    response_outcome = Column(String(50))  # e.g., "accepted", "rejected", "needs_follow_up"
    response_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Define relationships
    email = relationship(
        "Email",
        backref="batches",
        foreign_keys=[email_id]
    )
```

### Phone Call Models (`communication_service/models/phone_call.py`)

Two models were implemented to handle phone call scheduling and batch processing:

#### PhoneCall Model

```python
class PhoneCall(Base):
    """Phone call database model."""

    __tablename__ = "phone_calls"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=5)
    actual_date = Column(Date)
    actual_time = Column(Time)
    status = Column(String(50), default=PhoneCallStatus.SCHEDULED.value)
    outcome = Column(Text)
    notes = Column(Text)
    retry_after = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

#### PhoneCallBatch Model

```python
class PhoneCallBatch(Base):
    """Phone call batch database model."""

    __tablename__ = "phone_call_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    phone_call_id = Column(
        Integer,
        ForeignKey("communication_service.phone_calls.id", ondelete="CASCADE"),
        nullable=False
    )
    placement_request_id = Column(
        Integer,
        ForeignKey("matching_service.placement_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    priority = Column(Integer, default=1)
    discussed = Column(Boolean, default=False)
    outcome = Column(String(50))
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## API Implementation

### Flask Application (`communication_service/app.py`)

The main Flask application is configured with RESTful API endpoints:

```python
def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure email settings - using your local SMTP gateway
    app.config["SMTP_HOST"] = "127.0.0.1"
    app.config["SMTP_PORT"] = 1025
    app.config["SMTP_USERNAME"] = "therapieplatz@peterhaupt.de"
    app.config["SMTP_PASSWORD"] = "***REMOVED_EXPOSED_PASSWORD***"
    app.config["SMTP_USE_TLS"] = True
    app.config["EMAIL_SENDER"] = "therapieplatz@peterhaupt.de"
    app.config["EMAIL_SENDER_NAME"] = "Boona Therapieplatz-Vermittlung"

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints for emails
    api.add_resource(EmailListResource, '/api/emails')
    api.add_resource(EmailResource, '/api/emails/<int:email_id>')
    api.add_resource(EmailResponseResource, '/api/emails/<int:email_id>/response')
    api.add_resource(EmailBatchListResource, '/api/emails/<int:email_id>/batches')
    api.add_resource(EmailBatchResource, '/api/email-batches/<int:batch_id>')
    
    # Register API endpoints for phone calls
    api.add_resource(PhoneCallListResource, '/api/phone-calls')
    api.add_resource(PhoneCallResource, '/api/phone-calls/<int:call_id>')
    api.add_resource(PhoneCallBatchResource, '/api/phone-call-batches/<int:batch_id>')

    # Start Kafka consumers
    start_consumers()

    return app
```

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

### Implementation (`communication_service/utils/email_sender.py`):
- **can_contact_therapist()**: Enforces the 7-day frequency limitation
- **create_batch_email()**: Creates emails with multiple patient requests
- **process_pending_requests()**: Identifies requests that need to be batched
- **send_queued_emails()**: Processes the email queue with batch awareness

## Phone Call Scheduling System

The phone call scheduling system provides automated scheduling of calls based on therapist availability:

### Key Features:
- **Availability Parsing**: Converts therapist's JSON availability data into usable time slots
- **Slot Finding**: Locates appropriate time slots for scheduling calls
- **Follow-up Automation**: Automatically schedules follow-up calls for unanswered emails after 7 days
- **Batch Processing**: Handles multiple placement requests in a single call
- **5-Minute Intervals**: Schedules calls in 5-minute time blocks

### Implementation (`communication_service/utils/phone_call_scheduler.py`):
- **find_available_slot()**: Finds the next available time slot for a therapist
- **is_slot_booked()**: Checks if a time slot is already booked
- **schedule_call_for_email()**: Schedules a call for an unanswered email
- **schedule_follow_up_calls()**: Processes all emails that need follow-up calls

## Email Template System

The service uses a structured template system with Jinja2:

```
communication_service/
└── templates/
    └── emails/
        ├── base_email.html       # Base template with common structure
        ├── initial_contact.html  # Template for first contact with therapist
        ├── batch_request.html    # Template for multiple patient requests
        ├── follow_up.html        # Template for follow-up communications
        └── confirmation.html     # Template for confirming accepted patients
```

## Resilient Kafka Integration

A robust Kafka producer was implemented to handle connection issues and message persistence:

### Key Features:
- **Connection Retries**: Exponential backoff retry logic for connecting to Kafka
- **Message Persistence**: Local storage of messages when Kafka is unavailable
- **Background Processing**: Thread for sending queued messages when connection is restored
- **Error Handling**: Proper handling of various error conditions

### Implementation (`communication_service/events/robust_producer.py`):
- **RobustKafkaProducer**: Main class handling Kafka connection and message queuing
- **_connect_with_retry()**: Handles connection attempts with exponential backoff
- **_store_message()**: Persists messages to disk when Kafka is unavailable
- **_process_queue()**: Background thread for sending queued messages
- **send_event()**: Main method for sending events with fallback to queuing

## Event Handling

The service consumes matching events to track changes in placement requests:

### Implementation (`communication_service/events/consumers.py`):
- **handle_matching_event()**: Processes events from the matching service
- **process_email_queue()**: Regularly checks for emails that need to be sent
- **check_unanswered_emails()**: Identifies emails that need follow-up calls
- **schedule_daily_batch_processing()**: Runs the daily batch email processing

## Database Integration

The email batching system is supported by the database schema through these migrations:
- `5dfc91e6b6f9_create_communication_tables.py`: Created the initial email table
- `7bfc93a7c8e9_create_phone_call_tables.py`: Added the phone call tables
- `8bfc94a7d8f9_add_email_batch_table.py`: Added the email batch table and necessary fields to the email table