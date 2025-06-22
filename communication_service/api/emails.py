"""Email API endpoints implementation with markdown support and German field names."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import markdown2
import re

from models.email import Email, EmailStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from shared.config import get_config

# Get configuration
config = get_config()


# Custom field for enum serialization
class EnumField(fields.Raw):
    """Custom field for enum serialization that returns the enum value."""
    def format(self, value):
        if value is None:
            return None
        # If it's an enum, return its value
        if hasattr(value, 'value'):
            return value.value
        # If it's already a string (e.g., from request), return as is
        return value


# Custom field for datetime serialization
class DateTimeField(fields.Raw):
    """Custom field for datetime serialization."""
    def format(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        # Format datetime as ISO string
        return value.isoformat()


# Output fields definition for email responses (German field names)
email_fields = {
    'id': fields.Integer,
    'therapist_id': fields.Integer,
    'patient_id': fields.Integer,
    'betreff': fields.String,
    'inhalt_html': fields.String,
    'inhalt_text': fields.String,
    'empfaenger_email': fields.String,
    'empfaenger_name': fields.String,
    'absender_email': fields.String,
    'absender_name': fields.String,
    'antwort_erhalten': fields.Boolean,
    'antwortdatum': DateTimeField,
    'antwortinhalt': fields.String,
    'status': EnumField,
    'in_warteschlange_am': DateTimeField,
    'gesendet_am': DateTimeField,
    'fehlermeldung': fields.String,
    'wiederholungsanzahl': fields.Integer,
    'created_at': DateTimeField,
    'updated_at': DateTimeField,
}


def validate_and_get_email_status(status_value: str) -> EmailStatus:
    """Validate and return EmailStatus enum.
    
    Args:
        status_value: German status value from request
        
    Returns:
        EmailStatus enum
        
    Raises:
        ValueError: If status value is invalid
    """
    if not status_value:
        return None
    
    try:
        return EmailStatus[status_value]
    except KeyError:
        valid_values = [status.value for status in EmailStatus]
        raise ValueError(f"Invalid status '{status_value}'. Valid values: {valid_values}")


def parse_datetime_field(datetime_string: str, field_name: str):
    """Parse datetime string and return datetime object.
    
    Args:
        datetime_string: DateTime in ISO format
        field_name: Name of field for error messages
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If datetime format is invalid
    """
    if not datetime_string:
        return None
    
    try:
        return datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"Invalid datetime format for {field_name}. Use ISO format")


def convert_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown text to HTML with link detection.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        HTML string
    """
    if not markdown_text:
        return ""
    
    # First, detect and convert URLs to markdown links
    # This regex finds URLs that are not already in markdown link format
    url_pattern = r'(?<!\[)(?<!\()https?://[^\s\)]+(?!\))'
    
    def replace_url(match):
        url = match.group(0)
        # Remove trailing punctuation
        if url[-1] in '.,:;!?':
            url = url[:-1]
        return f'[{url}]({url})'
    
    # Replace URLs with markdown links
    text_with_links = re.sub(url_pattern, replace_url, markdown_text)
    
    # Convert to HTML with tables extension
    html = markdown2.markdown(
        text_with_links,
        extras=['tables', 'fenced-code-blocks']
    )
    
    return html


def convert_markdown_to_text(markdown_text: str) -> str:
    """Convert markdown to plain text.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        Plain text string
    """
    if not markdown_text:
        return ""
    
    # Remove markdown formatting
    text = markdown_text
    
    # Headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Bold and italic
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Lists
    text = re.sub(r'^\s*[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Tables (simple approach)
    text = re.sub(r'\|', ' ', text)
    text = re.sub(r'\n[\-\+]+\n', '\n', text)
    
    # Code blocks
    text = re.sub(r'```[^\n]*\n([^`]+)\n```', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    return text.strip()


def add_legal_footer(body_html: str, body_text: str) -> tuple:
    """Add legal footer to email content.
    
    Args:
        body_html: HTML body content
        body_text: Plain text body content
        
    Returns:
        Tuple of (html_with_footer, text_with_footer)
    """
    footer_html = """
    <hr style="margin-top: 40px; border: 1px solid #e0e0e0;">
    <p style="font-size: 12px; color: #666; margin-top: 20px;">
        <strong>Curavani Therapievermittlung GmbH</strong><br>
        Musterstraße 123, 12345 Berlin<br>
        Tel: +49 30 12345678 | E-Mail: info@curavani.de<br>
        Geschäftsführer: Max Mustermann | HRB 12345 Berlin<br>
        <br>
        Diese E-Mail kann vertrauliche Informationen enthalten. Falls Sie nicht der 
        beabsichtigte Empfänger sind, benachrichtigen Sie bitte den Absender und 
        löschen Sie diese E-Mail.
    </p>
    """
    
    footer_text = """
    
--
Curavani Therapievermittlung GmbH
Musterstraße 123, 12345 Berlin
Tel: +49 30 12345678 | E-Mail: info@curavani.de
Geschäftsführer: Max Mustermann | HRB 12345 Berlin

Diese E-Mail kann vertrauliche Informationen enthalten. Falls Sie nicht der 
beabsichtigte Empfänger sind, benachrichtigen Sie bitte den Absender und 
löschen Sie diese E-Mail.
    """
    
    return (body_html + footer_html, body_text + footer_text)


class EmailResource(Resource):
    """REST resource for individual email operations."""

    def get(self, email_id):
        """Get a specific email by ID."""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'message': 'Email not found'}, 404
            return marshal(email, email_fields)
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def put(self, email_id):
        """Update an existing email."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('antwort_erhalten', type=bool)
        parser.add_argument('antwortdatum', type=str)
        parser.add_argument('antwortinhalt', type=str)
        parser.add_argument('fehlermeldung', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'message': 'Email not found'}, 404
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status':
                        try:
                            email.status = validate_and_get_email_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'antwortdatum':
                        try:
                            email.antwortdatum = parse_datetime_field(value, key)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        setattr(email, key, value)
            
            # Update timestamp
            email.updated_at = datetime.utcnow()
            
            # Handle status-specific updates
            if email.status == EmailStatus.In_Warteschlange and not email.in_warteschlange_am:
                email.in_warteschlange_am = datetime.utcnow()
            elif email.status == EmailStatus.Gesendet and not email.gesendet_am:
                email.gesendet_am = datetime.utcnow()
            
            db.commit()
            db.refresh(email)
            
            return marshal(email, email_fields)
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, email_id):
        """Delete an email."""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'message': 'Email not found'}, 404
            
            db.delete(email)
            db.commit()
            
            return {'message': 'Email deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class EmailListResource(PaginatedListResource):
    """REST resource for email collection operations."""

    def get(self):
        """Get a list of emails with optional filtering and pagination."""
        # Parse query parameters for filtering
        therapist_id = request.args.get('therapist_id', type=int)
        patient_id = request.args.get('patient_id', type=int)
        recipient_type = request.args.get('recipient_type')
        status = request.args.get('status')
        
        db = SessionLocal()
        try:
            query = db.query(Email)
            
            # Apply filters if provided
            if therapist_id:
                query = query.filter(Email.therapist_id == therapist_id)
            
            if patient_id:
                query = query.filter(Email.patient_id == patient_id)
            
            if recipient_type:
                if recipient_type == 'therapist':
                    query = query.filter(Email.therapist_id.isnot(None))
                elif recipient_type == 'patient':
                    query = query.filter(Email.patient_id.isnot(None))
            
            if status:
                try:
                    status_enum = validate_and_get_email_status(status)
                    query = query.filter(Email.status == status_enum)
                except ValueError:
                    # If status value not found, return empty result
                    return {
                        "data": [],
                        "page": 1,
                        "limit": self.DEFAULT_LIMIT,
                        "total": 0
                    }
            
            # Order by created_at descending (newest first)
            query = query.order_by(Email.created_at.desc())
            
            # Use the new helper method
            return self.create_paginated_response(query, marshal, email_fields)
            
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def post(self):
        """Create a new email."""
        parser = reqparse.RequestParser()
        # Recipient (one required)
        parser.add_argument('therapist_id', type=int)
        parser.add_argument('patient_id', type=int)
        # Content
        parser.add_argument('betreff', type=str, required=True,
                          help='Betreff is required')
        parser.add_argument('inhalt_html', type=str)
        parser.add_argument('inhalt_text', type=str)
        parser.add_argument('inhalt_markdown', type=str)
        # Recipient details
        parser.add_argument('empfaenger_email', type=str, required=True,
                          help='Empfaenger email is required')
        parser.add_argument('empfaenger_name', type=str, required=True,
                          help='Empfaenger name is required')
        # Sender details (optional)
        parser.add_argument('absender_email', type=str)
        parser.add_argument('absender_name', type=str)
        # Options
        parser.add_argument('add_legal_footer', type=bool, default=True)
        
        try:
            args = parser.parse_args()
        except Exception as e:
            if hasattr(e, 'data') and 'message' in e.data:
                errors = []
                for field, msg in e.data['message'].items():
                    errors.append(f"{field}: {msg}")
                return {'message': ' '.join(errors)}, 400
            return {'message': str(e)}, 400
        
        # Validate recipient
        if not args.get('therapist_id') and not args.get('patient_id'):
            return {'message': 'Either therapist_id or patient_id is required'}, 400
        
        if args.get('therapist_id') and args.get('patient_id'):
            return {'message': 'Cannot specify both therapist_id and patient_id'}, 400
        
        # Validate content
        if not args.get('inhalt_html') and not args.get('inhalt_text') and not args.get('inhalt_markdown'):
            return {'message': 'Either inhalt_html, inhalt_text, or inhalt_markdown is required'}, 400
        
        db = SessionLocal()
        try:
            # Handle markdown content
            if args.get('inhalt_markdown'):
                html_content = convert_markdown_to_html(args['inhalt_markdown'])
                text_content = convert_markdown_to_text(args['inhalt_markdown'])
            else:
                html_content = args.get('inhalt_html', '')
                text_content = args.get('inhalt_text', '')
            
            # Add legal footer if requested
            if args.get('add_legal_footer', True):
                html_content, text_content = add_legal_footer(html_content, text_content)
            
            # Create new email
            email_data = {
                'therapist_id': args.get('therapist_id'),
                'patient_id': args.get('patient_id'),
                'betreff': args['betreff'],
                'inhalt_html': html_content,
                'inhalt_text': text_content,
                'empfaenger_email': args['empfaenger_email'],
                'empfaenger_name': args['empfaenger_name'],
                'absender_email': args.get('absender_email') or config.EMAIL_SENDER,
                'absender_name': args.get('absender_name') or config.EMAIL_SENDER_NAME,
                'status': EmailStatus.Entwurf,
                'antwort_erhalten': False,
                'wiederholungsanzahl': 0
            }
            
            email = Email(**email_data)
            
            db.add(email)
            db.commit()
            db.refresh(email)
            
            return marshal(email, email_fields), 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()