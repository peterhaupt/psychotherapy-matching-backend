"""Email API endpoints implementation with patient support."""
from datetime import datetime
from flask import request, current_app
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError
import logging

from models.email import Email, EmailStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from events.producers import publish_email_created, publish_email_sent
from utils.email_sender import send_email, get_smtp_settings


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


# Output fields definition for email responses - German field names
email_fields = {
    'id': fields.Integer,
    'therapist_id': fields.Integer,
    'patient_id': fields.Integer,  # NEW field
    'betreff': fields.String,
    'empfaenger_email': fields.String,
    'empfaenger_name': fields.String,
    'absender_email': fields.String,
    'absender_name': fields.String,
    'status': EnumField,  # Use custom field for enum
    'antwort_erhalten': fields.Boolean,
    'antwortdatum': fields.DateTime,
    'antwortinhalt': fields.String,
    'nachverfolgung_erforderlich': fields.Boolean,
    'gesendet_am': fields.DateTime,  # Updated field name
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
}


class EmailResource(Resource):
    """REST resource for individual email operations."""

    @marshal_with(email_fields)
    def get(self, email_id):
        """Get a specific email by ID."""
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'message': 'Email not found'}, 404
            return email
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
            
    @marshal_with(email_fields)
    def put(self, email_id):
        """Update an email."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('antwort_erhalten', type=bool)
        parser.add_argument('antwortdatum', type=str)
        parser.add_argument('antwortinhalt', type=str)
        parser.add_argument('nachverfolgung_erforderlich', type=bool)
        parser.add_argument('nachverfolgung_notizen', type=str)
        
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
                            email.status = EmailStatus(value)
                        except ValueError:
                            return {'message': f'Invalid status value: {value}'}, 400
                    elif key == 'antwortdatum' and value:
                        email.antwortdatum = datetime.fromisoformat(value)
                    else:
                        setattr(email, key, value)
            
            db.commit()
            return email
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class EmailListResource(PaginatedListResource):
    """REST resource for email collection operations with patient support."""

    @marshal_with(email_fields)
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
            if recipient_type == 'therapist' and therapist_id:
                query = query.filter(Email.therapist_id == therapist_id)
            elif recipient_type == 'patient' and patient_id:
                query = query.filter(Email.patient_id == patient_id)
            elif therapist_id:  # Backward compatibility
                query = query.filter(Email.therapist_id == therapist_id)
            elif patient_id:
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
            
            # Get results
            emails = query.all()
            return emails
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(email_fields)
    def post(self):
        """Create a new email with support for both therapist and patient recipients."""
        parser = reqparse.RequestParser()
        # Recipient fields - now both optional
        parser.add_argument('therapist_id', type=int, required=False)
        parser.add_argument('patient_id', type=int, required=False)  # NEW field
        
        # Required email fields - German names
        parser.add_argument('betreff', type=str, required=True,
                           help='Subject is required')
        parser.add_argument('inhalt_html', type=str, required=True,
                           help='HTML body is required')
        parser.add_argument('empfaenger_email', type=str, required=True,
                           help='Recipient email is required')
        parser.add_argument('empfaenger_name', type=str, required=True,
                           help='Recipient name is required')
        
        # Optional fields
        parser.add_argument('inhalt_text', type=str)
        parser.add_argument('absender_email', type=str)
        parser.add_argument('absender_name', type=str)
        parser.add_argument('status', type=str)
        
        args = parser.parse_args()
        
        # Validate that exactly one recipient type is specified
        if not args.get('therapist_id') and not args.get('patient_id'):
            return {'message': 'Either therapist_id or patient_id is required'}, 400
        if args.get('therapist_id') and args.get('patient_id'):
            return {'message': 'Cannot specify both therapist_id and patient_id'}, 400
        
        db = SessionLocal()
        try:
            logging.info(f"Creating email for {'therapist' if args.get('therapist_id') else 'patient'}_id={args.get('therapist_id') or args.get('patient_id')}")
            
            # Get email settings from centralized configuration
            smtp_settings = get_smtp_settings()
            
            # Create new email
            email = Email(
                therapist_id=args.get('therapist_id'),
                patient_id=args.get('patient_id'),
                betreff=args['betreff'],
                inhalt_html=args['inhalt_html'],
                inhalt_text=args.get('inhalt_text', ''),
                empfaenger_email=args['empfaenger_email'],
                empfaenger_name=args['empfaenger_name'],
                absender_email=args.get('absender_email') or smtp_settings['sender'],
                absender_name=args.get('absender_name') or smtp_settings['sender_name'],
            )
            # Let the status be set by the default in the model
            # This ensures we get the expected enum with German values
            db.add(email)
            db.commit()
            db.refresh(email)
            logging.debug(f"Email created with ID: {email.id}")
            
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
            
            return email, 201
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