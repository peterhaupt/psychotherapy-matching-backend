# Communication Service

## Summary
This document details the implementation of the Communication Service for the Psychotherapy Matching Platform. The service handles all communication-related operations including email management, template rendering, and message dispatching. It provides a foundation for both automated and manual communication with therapists.

## Current Status
The Communication Service has been partially implemented with these core components:

- **Email Model**: Database storage for emails with status tracking
- **API Endpoints**: Basic REST endpoints for email operations
- **Kafka Integration**: Event producers and consumers 
- **Email Sending Functionality**: Integrated SMTP client for email delivery
- **Template Rendering**: Simple Jinja2-based template system

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
    
    # Placement requests associated with this email
    placement_request_ids = Column(JSONB)
    
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

### Status Enumeration

The service defines an enumeration for email statuses:

```python
class EmailStatus(str, Enum):
    """Enumeration for email status values."""

    DRAFT = "entwurf"
    QUEUED = "in_warteschlange"
    SENDING = "wird_gesendet"
    SENT = "gesendet"
    FAILED = "fehlgeschlagen"
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
    
    # Configure email settings
    app.config["SMTP_HOST"] = "127.0.0.1"
    app.config["SMTP_PORT"] = 1025
    app.config["SMTP_USERNAME"] = "therapieplatz@peterhaupt.de"
    app.config["SMTP_PASSWORD"] = "***REMOVED_EXPOSED_PASSWORD***"
    app.config["SMTP_USE_TLS"] = True
    app.config["EMAIL_SENDER"] = "therapieplatz@peterhaupt.de"
    app.config["EMAIL_SENDER_NAME"] = "Boona Therapieplatz-Vermittlung"

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(EmailListResource, '/api/emails')
    api.add_resource(EmailResource, '/api/emails/<int:email_id>')

    # Start Kafka consumers
    start_consumers()

    return app
```

### API Endpoints (`communication_service/api/emails.py`)

The service implements RESTful endpoints for email management:

#### EmailResource
Handles individual email operations:
- `GET /api/emails/<id>`: Retrieve a specific email

#### EmailListResource
Handles collection operations:
- `GET /api/emails`: Retrieve all emails with optional filtering
- `POST /api/emails`: Create a new email

### Request Parsing and Validation

API endpoints use Flask-RESTful's `reqparse` for request parsing and validation:

```python
parser = reqparse.RequestParser()
# Required fields
parser.add_argument('therapist_id', type=int, required=True,
                   help='Therapist ID is required')
parser.add_argument('subject', type=str, required=True,
                   help='Subject is required')
parser.add_argument('body_html', type=str, required=True,
                   help='HTML body is required')
parser.add_argument('recipient_email', type=str, required=True,
                   help='Recipient email is required')
parser.add_argument('recipient_name', type=str, required=True,
                   help='Recipient name is required')
```

### Response Marshalling

Response data is consistently formatted using Flask-RESTful's marshalling:

```python
email_fields = {
    'id': fields.Integer,
    'therapist_id': fields.Integer,
    'subject': fields.String,
    'recipient_email': fields.String,
    'recipient_name': fields.String,
    'status': fields.String,
    'created_at': fields.DateTime,
    'sent_at': fields.DateTime,
}
```

## Event Management

### Event Producers (`communication_service/events/producers.py`)

The service implements Kafka producers for email-related events:

```python
def publish_email_created(email_id: int, email_data: Dict[str, Any]) -> bool:
    """Publish an event when a new email is created."""
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="communication.email_created",
        payload={
            "email_id": email_id,
            "email_data": email_data
        },
        key=str(email_id)
    )
```

Two main event types are published:
1. `communication.email_created`: When a new email is created
2. `communication.email_sent`: When an email is successfully sent

### Event Consumers (`communication_service/events/consumers.py`)

The service consumes events from the Matching service:

```python
def handle_matching_event(event: EventSchema) -> None:
    """Handle events from the matching service."""
    if event.event_type == "match.created":
        # This could trigger an email to be created
        logger.info("New match created, consider sending notification email")
        
    elif event.event_type == "match.status_changed":
        # This could trigger different types of emails depending on new status
        new_status = event.payload.get("new_status")
        logger.info(f"Match status changed to {new_status}")
```

Key event handling includes:
- Reacting to new matches to create contact emails
- Responding to status changes to send appropriate notifications

## Email Sending Functionality

### Email Sender (`communication_service/utils/email_sender.py`)

The service implements SMTP-based email sending:

```python
def send_email(email_id):
    """Send an email from the database."""
    # Get the email from the database
    email = db.query(Email).filter(Email.id == email_id).first()
    
    # Update status to SENDING
    email.status = EmailStatus.SENDING
    db.commit()
    
    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email.subject
    msg['From'] = f"{email.sender_name} <{email.sender_email}>"
    msg['To'] = f"{email.recipient_name} <{email.recipient_email}>"
    
    # Attach the plain text version
    text_part = MIMEText(email.body_text, 'plain')
    msg.attach(text_part)
    
    # Send the email via SMTP
    # ...
    
    # Update the email status
    email.status = EmailStatus.SENT
    email.sent_at = datetime.utcnow()
    db.commit()
```

### Email Queue Processing

The service includes a basic queue processing system:

```python
def send_queued_emails(limit=10):
    """Send queued emails."""
    # Get queued emails using SQLAlchemy with type casting
    from sqlalchemy import cast, String
    emails = db.query(Email).filter(
        cast(Email.status, String) == EmailStatus.QUEUED.value
    ).order_by(Email.queued_at).limit(limit).all()
    
    # Process emails
    sent_count = 0
    for email in emails:
        if send_email(email.id):
            sent_count += 1
    
    return sent_count
```

A background thread processes the email queue periodically:

```python
def email_queue_worker():
    import time
    while True:
        process_email_queue()
        time.sleep(60)  # Check every minute
```

## Template System

### Template Rendering (`communication_service/utils/template_renderer.py`)

A Jinja2-based template rendering system:

```python
def render_template(template_name, **context):
    """Render a template with the given context."""
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Failed to render template {template_name}: {str(e)}")
        raise
```

## Docker Configuration

### Dockerfile (`communication_service/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

EXPOSE 8004

CMD ["python", "app.py"]
```

## Database Migration

A migration script creates the email table in the `communication_service` schema:

```python
# Create EmailStatus enum type
email_status = sa.Enum(
    'entwurf', 'in_warteschlange', 'wird_gesendet', 'gesendet', 'fehlgeschlagen',
    name='emailstatus'
)

# Create emails table
op.create_table('emails',
    # Column definitions...
    sa.PrimaryKeyConstraint('id'),
    schema='communication_service'
)
```

## Remaining Tasks

The following components still need to be implemented:

1. **Email Templates**
   - Create HTML templates for different communication scenarios
   - Implement template customization based on request context
   - Add support for therapist-specific templates

2. **Email Batching Logic**
   - Implement the frequency limit of one email per therapist per week
   - Create batch email functionality to combine multiple patient requests
   - Add priority-based processing for different communication types

3. **Phone Call Scheduling**
   - Create database models for phone calls
   - Implement scheduling logic
   - Add reminder system
   - Implement call outcome tracking

4. **Integration Testing**
   - Develop comprehensive tests for email API endpoints
   - Test email sending functionality
   - Validate event-based email creation

5. **HTML Email Support**
   - Enhance the current email sending to fully support HTML content
   - Add rich formatting options
   - Implement email tracking capabilities

6. **Advanced Error Handling**
   - Improve retry logic for failed emails
   - Add more robust error reporting
   - Implement alerting for persistent failures

## Integration Plan

The Communication Service integrates with other services through:

1. **REST API**: For direct email creation by other services
2. **Kafka Events**: For event-based email creation in response to system events
3. **Database**: For tracking communication history and status

The service will be expanded to handle more complex communication scenarios as the platform evolves.