"""Email API endpoints implementation."""
from datetime import datetime
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from models.email import Email, EmailStatus
from shared.utils.database import SessionLocal
from events.producers import publish_email_created, publish_email_sent
from utils.email_sender import send_email


# Output fields definition for email responses
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


class EmailListResource(Resource):
    """REST resource for email collection operations."""

    @marshal_with(email_fields)
    def get(self):
        """Get a list of emails with optional filtering."""
        # Parse query parameters for filtering
        therapist_id = request.args.get('therapist_id', type=int)
        status = request.args.get('status')
        
        db = SessionLocal()
        try:
            query = db.query(Email)
            
            # Apply filters if provided
            if therapist_id:
                query = query.filter(Email.therapist_id == therapist_id)
            if status:
                query = query.filter(Email.status == EmailStatus(status))
            
            # Get results
            emails = query.all()
            return emails
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(email_fields)
    def post(self):
        """Create a new email."""
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
        
        # Optional fields
        parser.add_argument('body_text', type=str)
        parser.add_argument('sender_email', type=str)
        parser.add_argument('sender_name', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('placement_request_ids', type=list)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Create new email
            email = Email(
                therapist_id=args['therapist_id'],
                subject=args['subject'],
                body_html=args['body_html'],
                body_text=args.get('body_text', ''),
                recipient_email=args['recipient_email'],
                recipient_name=args['recipient_name'],
                sender_email=args.get('sender_email', 'therapieplatz@peterhaupt.de'),
                sender_name=args.get('sender_name', 'Boona Therapieplatz-Vermittlung'),
                placement_request_ids=args.get('placement_request_ids')
            )
            
            # Set status if provided, otherwise use default (DRAFT)
            if args.get('status'):
                email.status = EmailStatus(args['status'])
                
                # If status is QUEUED, set the queued_at timestamp
                if email.status == EmailStatus.QUEUED:
                    email.queued_at = datetime.utcnow()
            
            db.add(email)
            db.commit()
            db.refresh(email)
            
            # Publish event for email creation
            publish_email_created(email.id, {
                'therapist_id': email.therapist_id,
                'subject': email.subject,
                'status': email.status.value
            })
            
            # If status is QUEUED, try to send it immediately
            if email.status == EmailStatus.QUEUED:
                send_email(email.id)
            
            return email, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()