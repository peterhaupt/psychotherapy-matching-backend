"""Email API endpoints implementation with markdown support and German field names."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
import re
import logging

from models.email import Email, EmailStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from shared.config import get_config
from utils.markdown_processor import markdown_to_html, strip_html
from shared.api.retry_client import RetryAPIClient
# PHASE 2: Import event publishers
from events.producers import publish_email_sent, publish_email_response_received

# Get configuration
config = get_config()

# Set up logging
logger = logging.getLogger(__name__)


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


def preprocess_markdown_urls(markdown_text: str) -> str:
    """Detect and convert URLs to markdown links before processing.
    
    Args:
        markdown_text: Raw markdown text
        
    Returns:
        Markdown text with URLs converted to links
    """
    if not markdown_text:
        return ""
    
    # This regex finds URLs that are not already in markdown link format
    url_pattern = r'(?<!\[)(?<!\()https?://[^\s\)]+(?!\))'
    
    def replace_url(match):
        url = match.group(0)
        # Remove trailing punctuation
        if url[-1] in '.,:;!?':
            url = url[:-1]
        return f'[{url}]({url})'
    
    # Replace URLs with markdown links
    return re.sub(url_pattern, replace_url, markdown_text)


def convert_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown text to HTML with link detection.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        HTML string
    """
    if not markdown_text:
        return ""
    
    try:
        # First, detect and convert URLs to markdown links
        text_with_links = preprocess_markdown_urls(markdown_text)
        
        # Use the markdown processor utility
        html = markdown_to_html(text_with_links)
        
        return html
    except Exception as e:
        logger.error(f"Error converting markdown to HTML: {str(e)}", exc_info=True)
        raise


def convert_markdown_to_text(markdown_text: str) -> str:
    """Convert markdown to plain text.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        Plain text string
    """
    if not markdown_text:
        return ""
    
    try:
        # First convert to HTML
        html = convert_markdown_to_html(markdown_text)
        
        # Then strip HTML tags
        text = strip_html(html)
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error converting markdown to text: {str(e)}", exc_info=True)
        raise


def add_legal_footer(body_html: str, body_text: str) -> tuple:
    """Add legal footer to email content using centralized configuration.
    
    Args:
        body_html: HTML body content
        body_text: Plain text body content
        
    Returns:
        Tuple of (html_with_footer, text_with_footer)
    """
    config = get_config()
    
    footer_html = f"""
    <hr style="margin-top: 40px; border: 1px solid #e0e0e0;">
    <p style="font-size: 12px; color: #666; margin-top: 20px;">
        <strong>{config.COMPANY_NAME}</strong><br>
        {config.COMPANY_STREET}<br>
        {config.COMPANY_PLZ} {config.COMPANY_CITY}<br>
        {config.COMPANY_COUNTRY}<br>
        <br>
        E-Mail: {config.EMAIL_SENDER}<br>
        <br>
        Geschäftsführer: {config.COMPANY_CEO}<br>
        Handelsregister: {config.COMPANY_HRB}<br>
        <br>
        {config.LEGAL_FOOTER_PRIVACY_TEXT}
    </p>
    """
    
    footer_text = f"""
    
--
{config.COMPANY_NAME}
{config.COMPANY_STREET}
{config.COMPANY_PLZ} {config.COMPANY_CITY}
{config.COMPANY_COUNTRY}

E-Mail: {config.EMAIL_SENDER}

Geschäftsführer: {config.COMPANY_CEO}
Handelsregister: {config.COMPANY_HRB}

{config.LEGAL_FOOTER_PRIVACY_TEXT}
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
        """Update an existing email and notify patient service if needed."""
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
            
            # PHASE 2: Track status changes for events
            old_status = email.status
            old_antwort_erhalten = email.antwort_erhalten
            
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
            
            # PHASE 2: Publish events based on changes
            email_data_for_event = {
                'email_id': email.id,
                'therapist_id': email.therapist_id,
                'patient_id': email.patient_id,
                'betreff': email.betreff,
                'recipient_type': email.recipient_type,
                'status': email.status.value if hasattr(email.status, 'value') else str(email.status)
            }
            
            # Check if email was just sent
            if old_status != EmailStatus.Gesendet and email.status == EmailStatus.Gesendet:
                logger.info(f"Email {email_id} status changed to Gesendet, publishing event")
                publish_email_sent(email.id, email_data_for_event)
                
                # KAFKA REMOVAL: Update patient last contact via API
                if email.patient_id:
                    patient_service_url = config.get_service_url('patient', internal=True)
                    patient_url = f"{patient_service_url}/api/patients/{email.patient_id}/last-contact"
                    
                    try:
                        response = RetryAPIClient.call_with_retry(
                            method="PATCH",
                            url=patient_url,
                            json={"date": date.today().isoformat()}
                        )
                        if response.status_code == 200:
                            logger.info(f"Successfully updated patient {email.patient_id} last contact after email sent")
                        else:
                            logger.error(f"Failed to update patient last contact for patient {email.patient_id}: {response.status_code}")
                    except Exception as e:
                        # Log error but don't fail the email update
                        logger.error(f"Failed to update patient last contact for patient {email.patient_id}: {str(e)}")
            
            # Check if response was just received
            if not old_antwort_erhalten and email.antwort_erhalten:
                logger.info(f"Email {email_id} received response, publishing event")
                publish_email_response_received(email.id, email_data_for_event)
            
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
        # NEW: Accept status parameter for initial status
        parser.add_argument('status', type=str)
        
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
                logger.debug(f"Processing markdown content: {args['inhalt_markdown'][:100]}...")
                html_content = convert_markdown_to_html(args['inhalt_markdown'])
                text_content = convert_markdown_to_text(args['inhalt_markdown'])
            else:
                # Ensure we have strings, not None
                html_content = args.get('inhalt_html') or ''
                text_content = args.get('inhalt_text') or ''
            
            # Add legal footer if requested
            if args.get('add_legal_footer', True):
                html_content, text_content = add_legal_footer(html_content, text_content)
            
            # Determine initial status
            initial_status = EmailStatus.Entwurf  # default
            if args.get('status'):
                try:
                    initial_status = validate_and_get_email_status(args['status'])
                    logger.info(f"Setting initial email status to: {initial_status.value}")
                except ValueError as e:
                    return {'message': str(e)}, 400
            
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
                'status': initial_status,  # Use the provided or default status
                'antwort_erhalten': False,
                'wiederholungsanzahl': 0
            }
            
            # If status is In_Warteschlange, set the queued timestamp
            if initial_status == EmailStatus.In_Warteschlange:
                email_data['in_warteschlange_am'] = datetime.utcnow()
            
            email = Email(**email_data)
            
            db.add(email)
            db.commit()
            db.refresh(email)
            
            logger.info(f"Created email {email.id} with status {email.status.value}")
            
            return marshal(email, email_fields), 201
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating email: {str(e)}", exc_info=True)
            return {'message': f'Database error: {str(e)}'}, 500
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating email: {str(e)}", exc_info=True)
            return {'message': f'Internal server error: {str(e)}'}, 500
        finally:
            db.close()