# Communication Service Email Refactoring - Implementation Guide

## Overview

This guide refactors the Communication Service emails to be a pure formatting and delivery utility. Phone calls remain unchanged.

**Key Principle**: Communication Service handles presentation and delivery. Other services handle business content.

## Step 1: Update Dependencies

Add to `communication_service/requirements.txt`:
```
markdown==3.5.1
```

## Step 2: Update Configuration

### Update `shared/config.py`

Change company name and add legal footer configuration:

```python
# Change from 'Boona Team' to 'Curavani Team'
self.EMAIL_SENDER_NAME = os.environ.get('EMAIL_SENDER_NAME', 'Curavani Team')

# Add new configuration for legal footer
self.EMAIL_LEGAL_FOOTER = os.environ.get('EMAIL_LEGAL_FOOTER', '''
Diese E-Mail ist vertraulich und nur für den/die genannte(n) Empfänger bestimmt.
Falls Sie diese E-Mail irrtümlich erhalten haben, informieren Sie uns bitte und löschen Sie die Nachricht.

Curavani GmbH - Therapieplatz-Vermittlung
''')

# Add method to get legal footer
def get_email_legal_footer(self):
    """Get the email legal footer text."""
    return self.EMAIL_LEGAL_FOOTER
```

## Step 3: Create Content Processor

Create new file `communication_service/utils/content_processor.py`:

```python
"""Process email content from plain text or markdown to HTML."""
import markdown
import re
from html import escape


def process_email_content(inhalt_text, inhalt_markdown=None):
    """Convert plain text or markdown to HTML.
    
    Args:
        inhalt_text: Plain text content (required fallback)
        inhalt_markdown: Optional markdown content
        
    Returns:
        HTML content string
    """
    if inhalt_markdown:
        # Use markdown processor with useful extensions
        md = markdown.Markdown(extensions=[
            'tables',       # Support for tables
            'nl2br',        # Convert newlines to <br>
            'fenced_code',  # Code blocks with ```
        ])
        return md.convert(inhalt_markdown)
    else:
        # Convert plain text to HTML
        return text_to_html(inhalt_text)


def text_to_html(text):
    """Convert plain text to simple HTML.
    
    - Escapes HTML characters
    - Converts double newlines to paragraphs
    - Converts single newlines to <br>
    - Auto-links URLs
    """
    if not text:
        return ""
    
    # Escape HTML characters
    text = escape(text)
    
    # Auto-link URLs
    url_pattern = r'(https?://[^\s]+)'
    text = re.sub(url_pattern, r'<a href="\1">\1</a>', text)
    
    # Split into paragraphs (double newline)
    paragraphs = text.split('\n\n')
    html_paragraphs = []
    
    for para in paragraphs:
        if para.strip():
            # Convert single newlines to <br>
            para = para.replace('\n', '<br>\n')
            html_paragraphs.append(f'<p>{para}</p>')
    
    return '\n'.join(html_paragraphs)
```

## Step 4: Simplify Templates

### Delete Old Templates

Remove these files:
- `communication_service/templates/emails/batch_request.html`
- `communication_service/templates/emails/confirmation.html`
- `communication_service/templates/emails/follow_up.html`
- `communication_service/templates/emails/initial_contact.html`

### Update Base Template

Update `communication_service/templates/emails/base_email.html`:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
            border: 1px solid #dddddd;
            border-radius: 5px;
        }
        .header {
            padding: 15px 0;
            border-bottom: 2px solid #0056b3;
            margin-bottom: 20px;
        }
        .logo {
            font-size: 20px;
            font-weight: bold;
            color: #0056b3;
        }
        .content {
            padding: 20px 0;
        }
        /* Style markdown-generated elements */
        .content table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        .content th, .content td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .content th {
            background-color: #f2f2f2;
        }
        .content blockquote {
            border-left: 4px solid #0056b3;
            padding-left: 15px;
            margin: 15px 0;
            color: #666;
        }
        .content code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
        }
        .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #dddddd;
            font-size: 14px;
            color: #666666;
        }
        .legal {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            font-size: 12px;
            color: #666666;
            white-space: pre-line;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Curavani</div>
            <div style="font-size: 14px; color: #666;">Therapieplatz-Vermittlung</div>
        </div>
        
        <div class="content">
            {{ content_html | safe }}
        </div>
        
        <div class="footer">
            <p>Mit freundlichen Grüßen,<br>
            <strong>{{ sender_name }}</strong><br>
            E-Mail: {{ sender_email }}</p>
        </div>
        
        {% if include_legal %}
        <div class="legal">
            {{ legal_text }}
        </div>
        {% endif %}
    </div>
</body>
</html>
```

### Create Minimal Template

Create `communication_service/templates/emails/minimal.html`:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            color: #333333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .content p {
            margin: 10px 0;
        }
        .legal {
            margin-top: 40px;
            padding: 15px;
            background-color: #f5f5f5;
            font-size: 12px;
            color: #666666;
            border-top: 1px solid #ddd;
            white-space: pre-line;
        }
    </style>
</head>
<body>
    <div class="content">
        {{ content_html | safe }}
    </div>
    
    {% if include_legal %}
    <div class="legal">
        {{ legal_text }}
    </div>
    {% endif %}
</body>
</html>
```

## Step 5: Update Email API

### Update `communication_service/api/emails.py`

Add new fields to the POST endpoint:

```python
def post(self):
    """Create a new email with support for templates and markdown."""
    parser = reqparse.RequestParser()
    # Existing fields...
    parser.add_argument('therapist_id', type=int, required=False)
    parser.add_argument('patient_id', type=int, required=False)
    parser.add_argument('betreff', type=str, required=True)
    parser.add_argument('inhalt_html', type=str, required=True)
    parser.add_argument('empfaenger_email', type=str, required=True)
    parser.add_argument('empfaenger_name', type=str, required=True)
    parser.add_argument('inhalt_text', type=str)
    parser.add_argument('absender_email', type=str)
    parser.add_argument('absender_name', type=str)
    parser.add_argument('status', type=str)
    
    # NEW fields
    parser.add_argument('template', type=str, default='base_email')  # 'base_email' or 'minimal'
    parser.add_argument('inhalt_markdown', type=str)  # Optional markdown content
    parser.add_argument('skip_legal_footer', type=bool, default=False)
    
    args = parser.parse_args()
    
    # ... existing validation ...
    
    # Process content if markdown provided
    if args.get('inhalt_markdown'):
        from utils.content_processor import process_email_content
        from utils.template_renderer import render_template
        
        # Process markdown to HTML
        content_html = process_email_content(
            args.get('inhalt_text', ''), 
            args.get('inhalt_markdown')
        )
        
        # Render full HTML email
        template_name = args.get('template', 'base_email')
        if template_name not in ['base_email', 'minimal']:
            template_name = 'base_email'
        
        # Get config for legal text
        legal_text = config.get_email_legal_footer() if not args.get('skip_legal_footer') else None
        
        # Render template
        full_html = render_template(f'emails/{template_name}.html',
            subject=args['betreff'],
            content_html=content_html,
            sender_name=args.get('absender_name') or smtp_settings['sender_name'],
            sender_email=args.get('absender_email') or smtp_settings['sender'],
            include_legal=not args.get('skip_legal_footer'),
            legal_text=legal_text
        )
        
        # Update the HTML content
        args['inhalt_html'] = full_html
    
    # ... rest of existing code ...
```

## Step 6: Update Email Sender

### Update `communication_service/utils/email_sender.py`

No changes needed to the actual sending logic, but update any hardcoded "Boona" references to "Curavani".

## Step 7: Update Other Services

### Example: Matching Service Creating Bundle Email

Instead of sending full HTML, services now send simple content:

```python
# In matching_service/services.py or similar
def create_bundle_email_content(therapist_name, patients):
    """Create email content for bundle request."""
    
    # Create markdown content for rich formatting
    markdown_content = f"""
Sehr geehrte/r {therapist_name},

wir haben **{len(patients)} neue Therapieanfragen** für Sie:

| Patient | Diagnose | Verfügbarkeit | Krankenkasse |
|---------|----------|---------------|--------------|
"""
    
    for p in patients:
        markdown_content += f"| {p['vorname']} {p['nachname'][0]}. | {p['diagnose']} | {p['verfuegbarkeit']} | {p['krankenkasse']} |\n"
    
    markdown_content += """

Bitte teilen Sie uns mit, welche Patienten Sie übernehmen können.

> **Antwortfrist:** 7 Tage

Sie können direkt auf diese E-Mail antworten.
"""
    
    # Create plain text fallback
    plain_text = f"""
Sehr geehrte/r {therapist_name},

wir haben {len(patients)} neue Therapieanfragen für Sie:

"""
    for i, p in enumerate(patients, 1):
        plain_text += f"{i}. {p['vorname']} {p['nachname'][0]}. - {p['diagnose']}\n"
    
    plain_text += "\nBitte teilen Sie uns mit, welche Patienten Sie übernehmen können."
    
    # Send to communication service
    email_data = {
        'therapist_id': therapist_id,
        'template': 'base_email',  # Use standard template
        'betreff': f'Therapieanfrage für {len(patients)} Patienten',
        'inhalt_text': plain_text,
        'inhalt_markdown': markdown_content,
        'empfaenger_email': therapist_email,
        'empfaenger_name': therapist_name
    }
    
    # Call communication service API
    response = requests.post(f"{COMM_SERVICE_URL}/api/emails", json=email_data)
```

## Step 8: Testing

### Test Email Creation

```bash
# Test with markdown
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "template": "base_email",
    "betreff": "Test Email",
    "inhalt_text": "Simple text version",
    "inhalt_markdown": "**Bold** text with [link](https://curavani.de)",
    "empfaenger_email": "test@example.com",
    "empfaenger_name": "Dr. Test"
  }'

# Test minimal template
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 456,
    "template": "minimal",
    "betreff": "Terminerinnerung",
    "inhalt_text": "Ihre Therapiesitzung ist morgen um 14:00 Uhr.",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "Max Mustermann"
  }'
```

## Summary

1. **Email API** enhanced with `template`, `inhalt_markdown`, and `skip_legal_footer` fields
2. **Templates** simplified to just wrapper HTML with styling
3. **Content processing** handles markdown → HTML conversion
4. **Legal footer** automatically added (unless skipped)
5. **Other services** send plain/markdown content instead of HTML
6. **Phone calls** remain completely unchanged
7. **Company name** updated from Boona to Curavani

The Communication Service is now a pure utility service that knows nothing about business logic.