"""Email API endpoints implementation."""
from datetime import datetime
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from models.email import Email, EmailStatus
from models.email_batch import EmailBatch
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
    'response_received': fields.Boolean,
    'response_date': fields.DateTime,
    'batch_id': fields.String,
}

# Output fields for email batch information
email_batch_fields = {
    'id': fields.Integer,
    'email_id': fields.Integer,
    'placement_request_id': fields.Integer,
    'priority': fields.Integer,
    'included': fields.Boolean,
    'response_outcome': fields.String,
    'response_notes': fields.String,
    'created_at': fields.DateTime,
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
        parser.add_argument('response_received', type=bool)
        parser.add_argument('response_date', type=str)
        parser.add_argument('response_content', type=str)
        parser.add_argument('follow_up_required', type=bool)
        parser.add_argument('follow_up_notes', type=str)
        
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
                        email.status = EmailStatus(value)
                    elif key == 'response_date' and value:
                        email.response_date = datetime.fromisoformat(value)
                    else:
                        setattr(email, key, value)
            
            db.commit()
            return email
        except SQLAlchemyError as e:
            db.rollback()
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
        response_received = request.args.get('response_received', type=bool)
        batch_id = request.args.get('batch_id')
        
        db = SessionLocal()
        try:
            query = db.query(Email)
            
            # Apply filters if provided
            if therapist_id:
                query = query.filter(Email.therapist_id == therapist_id)
            if status:
                query = query.filter(Email.status == EmailStatus(status))
            if response_received is not None:
                query = query.filter(Email.response_received == response_received)
            if batch_id:
                query = query.filter(Email.batch_id == batch_id)
            
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
        parser.add_argument('batch_id', type=str)
        
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
                placement_request_ids=args.get('placement_request_ids'),
                batch_id=args.get('batch_id')
            )
            
            # Set status if provided, otherwise use default (DRAFT)
            if args.get('status'):
                email.status = EmailStatus(args['status'])
                
                # If status is QUEUED, set the queued_at timestamp
                if email.status == EmailStatus.QUEUED:
                    email.queued_at = datetime.utcnow()
            
            db.add(email)
            db.flush()  # Get ID without committing
            
            # Create email batches if placement_request_ids are provided
            placement_request_ids = args.get('placement_request_ids', [])
            for i, pr_id in enumerate(placement_request_ids):
                batch = EmailBatch(
                    email_id=email.id,
                    placement_request_id=pr_id,
                    priority=i + 1  # Priority based on order
                )
                db.add(batch)
            
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


class EmailResponseResource(Resource):
    """REST resource for tracking email responses."""
    
    @marshal_with(email_fields)
    def get(self, email_id):
        """Get response information for a specific email."""
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
        parser.add_argument('batch_id', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            logging.debug(f"Creating email for therapist_id={args['therapist_id']}")
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
                placement_request_ids=args.get('placement_request_ids'),
                batch_id=args.get('batch_id')
            )
            
            # Set status if provided, otherwise use default (DRAFT)
            if args.get('status'):
                logging.debug(f"Setting custom status: {args.get('status')}")
                email.status = EmailStatus(args['status'])
                
                # If status is QUEUED, set the queued_at timestamp
                if email.status == EmailStatus.QUEUED:
                    email.queued_at = datetime.utcnow()
            
            db.add(email)
            db.flush()  # Get ID without committing
            logging.debug(f"Email created with ID: {email.id}")
            
            # Create email batches if placement_request_ids are provided
            placement_request_ids = args.get('placement_request_ids', [])
            for i, pr_id in enumerate(placement_request_ids):
                batch = EmailBatch(
                    email_id=email.id,
                    placement_request_id=pr_id,
                    priority=i + 1  # Priority based on order
                )
                db.add(batch)
                logging.debug(f"Added batch for placement_request_id={pr_id}")
            
            db.commit()
            db.refresh(email)
            logging.debug(f"Database transaction committed")
            
            # Publish event for email creation
            logging.debug(f"About to publish email_created event for email_id={email.id}")
            try:
                result = publish_email_created(email.id, {
                    'therapist_id': email.therapist_id,
                    'subject': email.subject,
                    'status': email.status.value
                })
                logging.debug(f"Event published, result={result}")
            except Exception as e:
                logging.error(f"Error publishing email_created event: {e}", exc_info=True)
            
            # If status is QUEUED, try to send it immediately
            if email.status == EmailStatus.QUEUED:
                logging.debug(f"Email is queued, attempting to send immediately")
                send_email(email.id)
            
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


class EmailBatchListResource(Resource):
    """REST resource for email batch collection operations."""
    
    @marshal_with(email_batch_fields)
    def get(self, email_id):
        """Get all batches for a specific email."""
        db = SessionLocal()
        try:
            batches = db.query(EmailBatch).filter(
                EmailBatch.email_id == email_id
            ).all()
            
            if not batches:
                return []
                
            return batches
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
            
    @marshal_with(email_batch_fields)
    def post(self, email_id):
        """Add a placement request to an email batch."""
        parser = reqparse.RequestParser()
        parser.add_argument('placement_request_id', type=int, required=True,
                           help='Placement request ID is required')
        parser.add_argument('priority', type=int)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Check if email exists
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'message': 'Email not found'}, 404
                
            # Check if batch already exists
            existing_batch = db.query(EmailBatch).filter(
                EmailBatch.email_id == email_id,
                EmailBatch.placement_request_id == args['placement_request_id']
            ).first()
            
            if existing_batch:
                return {'message': 'This placement request is already in the batch'}, 400
                
            # Create new batch
            batch = EmailBatch(
                email_id=email_id,
                placement_request_id=args['placement_request_id'],
                priority=args.get('priority', 1)
            )
            
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
            return batch, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class EmailBatchResource(Resource):
    """REST resource for individual email batch operations."""
    
    @marshal_with(email_batch_fields)
    def get(self, batch_id):
        """Get a specific email batch."""
        db = SessionLocal()
        try:
            batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id).first()
            if not batch:
                return {'message': 'Email batch not found'}, 404
            return batch
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
    
    @marshal_with(email_batch_fields)
    def put(self, batch_id):
        """Update a specific email batch."""
        parser = reqparse.RequestParser()
        parser.add_argument('priority', type=int)
        parser.add_argument('included', type=bool)
        parser.add_argument('response_outcome', type=str)
        parser.add_argument('response_notes', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id).first()
            if not batch:
                return {'message': 'Email batch not found'}, 404
                
            # Update batch fields
            for key, value in args.items():
                if value is not None:
                    setattr(batch, key, value)
            
            db.commit()
            return batch
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
    
    def delete(self, batch_id):
        """Remove a placement request from an email batch."""
        db = SessionLocal()
        try:
            batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id).first()
            if not batch:
                return {'message': 'Email batch not found'}, 404
                
            db.delete(batch)
            db.commit()
            
            return {'message': 'Email batch deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()