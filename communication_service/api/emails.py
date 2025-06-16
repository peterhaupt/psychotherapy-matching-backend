"""Email API endpoints implementation with patient support and markdown support."""
from datetime import datetime
from flask import request, current_app
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
import logging

from models.email import Email, EmailStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from events.producers import publish_email_created, publish_email_sent
from utils.email_sender import send_email, get_smtp_settings
from utils.markdown_processor import markdown_to_html, strip_html, wrap_with_styling


# Custom field to properly handle enum values
class EnumField(fields.String):
    """Field that correctly marshals Enum types."""
    def format(self, value):
        """Format the enum value."""
        if value is None:
            return None
        # If it's an enum with value attribute, return that
        if hasattr(value, 'value'):
            return value.value
        # Otherwise convert to string
        return str(value)


# Custom field for nullable foreign keys
class NullableIntegerField(fields.Raw):
    """Field that properly handles nullable integers."""
    def format(self, value):
        """Format the value, returning None for null/0 values."""
        if value is None or value == 0:
            return None
        return value


# Output fields definition for email responses - German field names
# REMOVED: nachverfolgung_erforderlich and nachverfolgung_notizen fields
email_fields = {
    'id': fields.Integer,
    'therapist_id': NullableIntegerField,  # Use custom field
    'patient_id': NullableIntegerField,    # Use custom field
    'betreff': fields.String,
    'empfaenger_email': fields.String,
    'empfaenger_name': fields.String,
    'absender_email': fields.String,
    'absender_name': fields.String,
    'status': EnumField,  # Use custom field for enum
    'antwort_erhalten': fields.Boolean,
    'antwortdatum': fields.DateTime,
    'antwortinhalt': fields.String,
    'gesendet_am': fields.DateTime,  # Updated field name
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
}


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
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
            
    def put(self, email_id):
        """Update an email."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('antwort_erhalten', type=bool)
        parser.add_argument('antwortdatum', type=str)
        parser.add_argument('antwortinhalt', type=str)
        # REMOVED: nachverfolgung_erforderlich and nachverfolgung_notizen arguments
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'message': 'Email not found'}, 404
                
            # Update email fields
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        try:
                            # Convert string to EmailStatus enum
                            email.status = EmailStatus(value)
                        except ValueError:
                            return {'message': f'Invalid status value: {value}'}, 400
                    elif key == 'antwortdatum' and value:
                        try:
                            email.antwortdatum = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            return {'message': f'Invalid datetime format for antwortdatum: {value}'}, 400
                    else:
                        setattr(email, key, value)
            
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
    """REST resource for email collection operations with patient support."""

    def get(self):
        """Get a list of emails with optional filtering and pagination."""
        # Parse query parameters for filtering
        therapist_id = request.args.get('therapist_id', type=int)
        patient_id = request.args.get('patient_id', type=int)  # NEW parameter
        recipient_type = request.args.get('recipient_type')  # NEW parameter: 'therapist' or 'patient'
        status = request.args.get('status')
        antwort_erhalten = request.args.get('antwort_erhalten', type=bool)
        
        db = SessionLocal()
        try:
            query = db.query(Email)
            
            # Apply filters based on recipient type
            if recipient_type == 'therapist':
                # Filter for emails to therapists (therapist_id NOT NULL, patient_id NULL)
                query = query.filter(Email.therapist_id.isnot(None))
                query = query.filter(Email.patient_id.is_(None))
                if therapist_id:
                    query = query.filter(Email.therapist_id == therapist_id)
            elif recipient_type == 'patient':
                # Filter for emails to patients (patient_id NOT NULL, therapist_id NULL)
                query = query.filter(Email.patient_id.isnot(None))
                query = query.filter(Email.therapist_id.is_(None))
                if patient_id:
                    query = query.filter(Email.patient_id == patient_id)
            else:
                # No recipient_type specified, use individual filters
                if therapist_id:
                    query = query.filter(Email.therapist_id == therapist_id)
                if patient_id:
                    query = query.filter(Email.patient_id == patient_id)
            
            if status:
                try:
                    query = query.filter(Email.status == EmailStatus(status))
                except ValueError:
                    # Invalid status value, skip filter
                    pass
            
            if antwort_erhalten is not None:
                query = query.filter(Email.antwort_erhalten == antwort_erhalten)
            
            # Apply pagination
            query = self.paginate_query(query)
            
            # Get results and marshal
            emails = query.all()
            return [marshal(email, email_fields) for email in emails]
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def post(self):
        """Create a new email with support for both therapist and patient recipients, and markdown support."""
        parser = reqparse.RequestParser()
        # Recipient fields - now both optional
        parser.add_argument('therapist_id', type=int, required=False)
        parser.add_argument('patient_id', type=int, required=False)  # NEW field
        
        # Required email fields - German names
        parser.add_argument('betreff', type=str, required=True,
                           help='Subject is required')
        
        # Email body - either markdown OR HTML/text
        parser.add_argument('inhalt_markdown', type=str)  # NEW field for markdown
        parser.add_argument('inhalt_html', type=str)
        parser.add_argument('inhalt_text', type=str)
        
        parser.add_argument('empfaenger_email', type=str, required=True,
                           help='Recipient email is required')
        parser.add_argument('empfaenger_name', type=str, required=True,
                           help='Recipient name is required')
        
        # Optional fields
        parser.add_argument('absender_email', type=str)
        parser.add_argument('absender_name', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('add_legal_footer', type=bool, default=True)  # NEW field
        
        args = parser.parse_args()
        
        # Validate that exactly one recipient type is specified
        if not args.get('therapist_id') and not args.get('patient_id'):
            return {'message': 'Either therapist_id or patient_id is required'}, 400
        if args.get('therapist_id') and args.get('patient_id'):
            return {'message': 'Cannot specify both therapist_id and patient_id'}, 400
        
        # Validate that either markdown OR HTML is provided
        if not args.get('inhalt_markdown') and not args.get('inhalt_html'):
            return {'message': 'Either inhalt_markdown or inhalt_html is required'}, 400
        
        # Validate status if provided
        if args.get('status'):
            # Only allow user-settable statuses
            allowed_statuses = [EmailStatus.Entwurf.value, EmailStatus.In_Warteschlange.value]
            if args['status'] not in allowed_statuses:
                return {
                    'message': f"Invalid status. Only '{EmailStatus.Entwurf.value}' or '{EmailStatus.In_Warteschlange.value}' allowed"
                }, 400
        
        db = SessionLocal()
        try:
            logging.info(f"Creating email for {'therapist' if args.get('therapist_id') else 'patient'}_id={args.get('therapist_id') or args.get('patient_id')}")
            
            # Get email settings from centralized configuration
            smtp_settings = get_smtp_settings()
            
            # Process body content
            if args.get('inhalt_markdown'):
                # Convert markdown to HTML
                raw_html = markdown_to_html(args['inhalt_markdown'])
                body_html = wrap_with_styling(raw_html, args.get('add_legal_footer', True))
                body_text = strip_html(raw_html)
            else:
                # Use provided HTML/text
                body_html = args['inhalt_html']
                body_text = args.get('inhalt_text', '')
                
                # If add_legal_footer is requested and HTML is provided
                if args.get('add_legal_footer', True) and body_html:
                    body_html = wrap_with_styling(body_html, True)
            
            # Create new email
            email = Email(
                therapist_id=args.get('therapist_id'),
                patient_id=args.get('patient_id'),
                betreff=args['betreff'],
                inhalt_html=body_html,
                inhalt_text=body_text,
                empfaenger_email=args['empfaenger_email'],
                empfaenger_name=args['empfaenger_name'],
                absender_email=args.get('absender_email') or smtp_settings['sender'],
                absender_name=args.get('absender_name') or smtp_settings['sender_name'],
            )
            
            # Set status if provided and validated
            if args.get('status'):
                email.status = EmailStatus(args['status'])
            # Otherwise, the default from the model (Entwurf) will be used
            
            db.add(email)
            db.commit()
            db.refresh(email)
            logging.debug(f"Email created with ID: {email.id}, status: {email.status.value}")
            
            # Get status value safely for the event
            status_value = email.status.value if hasattr(email.status, 'value') else str(email.status)
            
            # Publish event for email creation
            logging.debug(f"About to publish email_created event for email_id={email.id}")
            try:
                result = publish_email_created(email.id, {
                    'therapist_id': email.therapist_id,
                    'patient_id': email.patient_id,
                    'recipient_type': email.recipient_type,
                    'betreff': email.betreff,
                    'status': status_value
                })
                logging.debug(f"Event published, result={result}")
            except Exception as e:
                logging.error(f"Error publishing email_created event: {e}", exc_info=True)
            
            # Update patient's last contact date if this is a patient email
            if email.patient_id:
                try:
                    import requests
                    from shared.config import get_config
                    config = get_config()
                    patient_service_url = config.get_service_url('patient', internal=True)
                    
                    # Update patient's letzter_kontakt field
                    response = requests.put(
                        f"{patient_service_url}/api/patients/{email.patient_id}",
                        json={'letzter_kontakt': datetime.utcnow().date().isoformat()}
                    )
                    if response.ok:
                        logging.info(f"Updated patient {email.patient_id} last contact date")
                except Exception as e:
                    logging.warning(f"Failed to update patient last contact date: {e}")
            
            return marshal(email, email_fields), 201
        except SQLAlchemyError as e:
            db.rollback()
            logging.error(f"Database error creating email: {str(e)}", exc_info=True)
            return {'message': f'Database error: {str(e)}'}, 500
        except Exception as e:
            db.rollback()
            logging.error(f"Unexpected error creating email: {str(e)}", exc_info=True)
            return {'message': f'Error: {str(e)}'}, 500
        finally:
            db.close()