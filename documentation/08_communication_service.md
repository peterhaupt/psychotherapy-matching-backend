# Communication Service

## Summary
This document details the implementation of the Communication Service for the Psychotherapy Matching Platform. The service handles all communication-related operations including email management, template rendering, and message dispatching. It provides a foundation for both automated and manual communication with therapists.

## Current Status
The Communication Service has been partially implemented with these components:

- **Email Model**: Database storage for emails with status tracking
- **API Endpoints**: Basic REST endpoints for email operations
- **Kafka Integration**: Event producers and consumers 
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

The service implements RESTful endpoints for email management with these core endpoints:
- `GET /api/emails/<id>`: Retrieve a specific email
- `GET /api/emails`: Retrieve all emails with optional filtering
- `POST /api/emails`: Create a new email

## Email Template System

### Template Structure
The service now uses a structured template system with Jinja2:

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

### Template Features
- **Base Template**: Common HTML structure with styling
- **Template Inheritance**: All email templates extend the base template
- **Responsive Design**: Mobile-friendly email templates
- **Batch Support**: Templates handle both single and multiple patient requests
- **Plain Text Fallback**: Automatic generation of plain text versions

### Template Rendering
The enhanced template renderer (`utils/template_renderer.py`) provides:
- Template selection based on email type and context
- HTML and plain text rendering options
- Global template variables and functions
- Error handling and logging

## Email Sending Functionality

### SMTP Integration
The service connects to an SMTP server to send emails with:
- TLS encryption support
- Authentication handling
- Configuration via Flask app settings

### Email Queue Processing
The service includes a system for processing the email queue:
- Batch processing of queued emails
- Status tracking and error handling
- Retry mechanism for failed emails

## Remaining Tasks

The following components still need to be implemented:

1. **Email Batching Logic**
   - Implement the frequency limit of one email per therapist per week
   - Add priority-based processing for different communication types

2. **Phone Call Scheduling**
   - Create database models for phone calls
   - Implement scheduling logic
   - Add reminder system
   - Implement call outcome tracking

3. **Integration Testing**
   - Develop comprehensive tests for email API endpoints
   - Test email sending functionality
   - Validate event-based email creation

4. **Advanced Error Handling**
   - Further improve retry logic for failed emails
   - Add more robust error reporting
   - Implement alerting for persistent failures