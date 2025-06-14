# Communication Service Migration Guide

## Overview
This guide outlines the migration of the Communication Service from a business-logic-heavy implementation to a pure infrastructure service. This is for a **DEVELOPMENT SYSTEM** - all test data will be deleted, and no backward compatibility is required.

## Migration Goals
1. Remove all business logic from Communication Service
2. Move template management to requesting services
3. Move scheduling algorithms to Matching/Therapist services  
4. Implement Markdown support and legal footer injection
5. Simplify to pure send/track functionality

## Pre-Migration Checklist
- [ ] Stop all services: `docker-compose down`
- [ ] Ensure you have latest code from all repositories
- [ ] Have a backup of the current `001_initial_setup.py` file

---

## Phase 1: Database Reset and Migration

### Step 1.1: Delete Existing Database
```bash
# Stop all services
docker-compose down

# Remove the database volume completely
docker-compose down -v

# This will delete ALL data - make sure this is what you want!
```

### Step 1.2: Create New Migration File
**Replace entire file: `migrations/alembic/versions/001_initial_setup.py`**

The new migration file should have these changes in the communication_service schema:

**Email table changes:**
- Remove: `nachverfolgung_erforderlich` column
- Remove: `nachverfolgung_notizen` column

**Phone call table changes:**
- Remove: `wiederholen_nach` column

All other tables and columns remain the same.

### Step 1.3: Start Fresh Database and Run Migration
```bash
# Start only the database services
docker-compose up -d postgres pgbouncer

# Wait for postgres to be ready (about 10 seconds)
sleep 10

# Run the new migration
cd migrations
alembic upgrade head

# Verify the migration
docker-compose exec postgres psql -U $DB_USER -d therapy_platform -c "\dt *.*"
```

---

## Phase 2: Update Communication Service Code

### Step 2.1: Update Models
**File: `communication_service/models/email.py`**
```python
# Remove these lines from the Email class:
nachverfolgung_erforderlich = Column(Boolean, default=False)
nachverfolgung_notizen = Column(Text)

# Remove these methods if they exist:
# - Any methods that reference nachverfolgung_erforderlich
# - Any methods that reference nachverfolgung_notizen
```

**File: `communication_service/models/phone_call.py`**
```python
# Remove this line from the PhoneCall class:
wiederholen_nach = Column(Date)

# Update the mark_as_failed method to remove retry_date parameter:
def mark_as_failed(self, notes: Optional[str] = None) -> None:
    """Mark the phone call as failed.
    
    Args:
        notes: Reason for failure
    """
    self.status = PhoneCallStatus.fehlgeschlagen.value
    if notes:
        self.notizen = notes
    self.updated_at = datetime.utcnow()
```

### Step 2.2: Add Dependencies
**File: `communication_service/requirements.txt`**
```txt
Flask==3.1.0
Flask-RESTful==0.3.10
flask-cors==4.0.0
SQLAlchemy==2.0.40
psycopg2-binary==2.9.10
flask-sqlalchemy==3.1.1
kafka-python==2.1.5
Jinja2==3.1.6
aiosmtplib==2.0.1
email-validator==2.0.0.post2
requests==2.31.0
# New dependencies for markdown and HTML processing
markdown-it-py==3.0.0
beautifulsoup4==4.12.3
```

### Step 2.3: Create New Utilities
**New File: `communication_service/utils/markdown_processor.py`**
```python
"""Markdown processing utilities."""
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup
from typing import Optional

# Initialize markdown processor with useful plugins
md = MarkdownIt("commonmark", {"breaks": True, "html": True})
md.enable(["table", "strikethrough"])

def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        HTML formatted text
    """
    return md.render(markdown_text)

def strip_html(html_text: str) -> str:
    """Strip HTML tags to create plain text.
    
    Args:
        html_text: HTML formatted text
        
    Returns:
        Plain text without HTML tags
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n').strip()

def wrap_with_styling(html_content: str, add_footer: bool = True) -> str:
    """Wrap HTML content with styling and optional footer.
    
    Args:
        html_content: Raw HTML content
        add_footer: Whether to add legal footer
        
    Returns:
        Styled HTML with optional footer
    """
    from shared.config import get_config
    config = get_config()
    
    footer_html = ""
    if add_footer and config.EMAIL_ADD_LEGAL_FOOTER:
        footer_html = get_legal_footer()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{ color: #2c5aa0; }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="content">
            {html_content}
        </div>
        {footer_html}
    </body>
    </html>
    """

def get_legal_footer() -> str:
    """Get the legal footer HTML."""
    return """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666;">
        <p><strong>Datenschutzhinweis:</strong> Diese E-Mail enthält vertrauliche und/oder gesundheitsbezogene Informationen und ist ausschließlich für den Adressaten bestimmt.</p>
        <p>© 2025 Boona Therapievermittlung GmbH<br>
        Musterstraße 123, 12345 Berlin<br>
        <a href="https://boona.de/datenschutz">Datenschutz</a> | 
        <a href="https://boona.de/impressum">Impressum</a> | 
        <a href="https://boona.de/kontakt">Kontakt</a></p>
    </div>
    """
```

### Step 2.4: Update Email API
**File: `communication_service/api/emails.py`**

Update the POST endpoint to accept markdown:
```python
def post(self):
    """Create a new email with markdown support."""
    parser = reqparse.RequestParser()
    # Existing fields...
    parser.add_argument('body_markdown', type=str)  # New field
    parser.add_argument('add_legal_footer', type=bool, default=True)  # New field
    
    # In the processing logic:
    from utils.markdown_processor import markdown_to_html, strip_html, wrap_with_styling
    
    # Convert markdown to HTML if provided
    if args.get('body_markdown'):
        raw_html = markdown_to_html(args['body_markdown'])
        body_html = wrap_with_styling(raw_html, args.get('add_legal_footer', True))
        body_text = strip_html(raw_html)
    else:
        # Use provided HTML/text as before
        body_html = args['inhalt_html']
        body_text = args.get('inhalt_text', '')
```

### Step 2.5: Remove Business Logic
**File: `communication_service/utils/email_sender.py`**
- Remove: `can_contact_therapist()` function
- Remove: `MIN_DAYS_BETWEEN_EMAILS` constant
- Remove: Any frequency checking logic

**File: `communication_service/utils/phone_call_scheduler.py`**
- Remove: All scheduling algorithm functions
- Keep only: Basic database operations

**File: `communication_service/events/consumers.py`**
- Remove: `check_unanswered_emails_worker()` function
- Remove: Automated follow-up logic
- Keep only: Basic event handling for send requests

### Step 2.6: Update Configuration
**File: `shared/config/settings.py`**
```python
# Add new configuration option
EMAIL_ADD_LEGAL_FOOTER: bool = os.environ.get("EMAIL_ADD_LEGAL_FOOTER", "true").lower() == "true"
```

---

## Phase 3: Update Other Services

### Step 3.1: Move Templates to Matching Service
**New Directory: `matching_service/templates/`**

Move all template files from `communication_service/templates/` to `matching_service/templates/`.

### Step 3.2: Update Matching Service Bundle Creation
**File: `matching_service/services.py`**

Update `CommunicationService.create_bundle_email()` to:
1. Generate markdown content instead of HTML
2. Remove template references
3. Use new markdown field in API call

### Step 3.3: Update Patient Service Communication
**File: `patient_service/utils/communication.py`**

Update all email functions to:
1. Generate markdown content
2. Use `body_markdown` field instead of `body_html`
3. Remove template parameters

---

## Phase 4: Testing

### Step 4.1: Start All Services
```bash
# Rebuild all images with new dependencies
docker-compose build

# Start all services
docker-compose up -d

# Check logs for errors
docker-compose logs -f
```

### Step 4.2: Test Email Creation
```bash
# Test markdown email
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "betreff": "Test Markdown Email",
    "body_markdown": "# Hello\n\nThis is a **test** email with:\n\n- Bullet points\n- *Italic text*\n- [Links](https://example.com)",
    "empfaenger_email": "test@example.com",
    "empfaenger_name": "Test User"
  }'
```

### Step 4.3: Test Phone Call Creation
```bash
# Test simple phone call (no auto-scheduling)
curl -X POST http://localhost:8004/api/phone-calls \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 1,
    "geplantes_datum": "2025-06-20",
    "geplante_zeit": "14:00",
    "notizen": "Follow-up call"
  }'
```

---

## Phase 5: Cleanup

### Step 5.1: Remove Unused Files
```bash
# Remove template directory from communication service
rm -rf communication_service/templates/

# Remove unused utility functions
# (Manual review of utils/ directory recommended)
```

### Step 5.2: Update Documentation
- Update API_REFERENCE.md to reflect removed fields
- Update service documentation to reflect new responsibilities
- Add examples of markdown usage

---

## Rollback Plan

If issues arise:
1. Stop all services: `docker-compose down`
2. Restore original `001_initial_setup.py`
3. Delete database volume: `docker-compose down -v`
4. Restore original code from git
5. Rebuild and restart

---

## Success Criteria

- [ ] Communication service starts without errors
- [ ] Emails can be created with markdown content
- [ ] Legal footer appears in emails when enabled
- [ ] Phone calls can be created with specific date/time
- [ ] No automated follow-up calls are created
- [ ] No frequency limiting on emails
- [ ] Other services can create communications successfully