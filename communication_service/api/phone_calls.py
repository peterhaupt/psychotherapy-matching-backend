"""Phone call API endpoints implementation."""
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from models.phone_call import PhoneCall, PhoneCallStatus, PhoneCallBatch
from shared.utils.database import SessionLocal
from utils.phone_call_scheduler import find_available_slot

# Output fields definition for phone call responses
phone_call_fields = {
    'id': fields.Integer,
    'therapist_id': fields.Integer,
    'scheduled_date': fields.String,
    'scheduled_time': fields.String,
    'duration_minutes': fields.Integer,
    'actual_date': fields.String,
    'actual_time': fields.String,
    'status': fields.String,
    'outcome': fields.String,
    'notes': fields.String,
    'retry_after': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
}

# Output fields for phone call batch responses
phone_call_batch_fields = {
    'id': fields.Integer,
    'phone_call_id': fields.Integer,
    'placement_request_id': fields.Integer,
    'priority': fields.Integer,
    'discussed': fields.Boolean,
    'outcome': fields.String,
    'follow_up_required': fields.Boolean,
    'follow_up_notes': fields.String,
    'created_at': fields.DateTime
}


class PhoneCallResource(Resource):
    """REST resource for individual phone call operations."""

    @marshal_with(phone_call_fields)
    def get(self, call_id):
        """Get a specific phone call by ID."""
        db = SessionLocal()
        try:
            phone_call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
            if not phone_call:
                return {'message': 'Phone call not found'}, 404
            return phone_call
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(phone_call_fields)
    def put(self, call_id):
        """Update an existing phone call."""
        parser = reqparse.RequestParser()
        parser.add_argument('scheduled_date', type=str)
        parser.add_argument('scheduled_time', type=str)
        parser.add_argument('duration_minutes', type=int)
        parser.add_argument('actual_date', type=str)
        parser.add_argument('actual_time', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('outcome', type=str)
        parser.add_argument('notes', type=str)
        parser.add_argument('retry_after', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            phone_call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
            if not phone_call:
                return {'message': 'Phone call not found'}, 404
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        # Make sure the status value is a valid enum value
                        if value not in [e.value for e in PhoneCallStatus]:
                            return {'message': f'Invalid status value: {value}'}, 400
                        phone_call.status = value
                    else:
                        setattr(phone_call, key, value)
            
            db.commit()
            return phone_call
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, call_id):
        """Delete a phone call."""
        db = SessionLocal()
        try:
            phone_call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
            if not phone_call:
                return {'message': 'Phone call not found'}, 404
            
            db.delete(phone_call)
            db.commit()
            
            return {'message': 'Phone call deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class PhoneCallListResource(Resource):
    """REST resource for phone call collection operations."""

    @marshal_with(phone_call_fields)
    def get(self):
        """Get a list of phone calls with optional filtering."""
        # Parse query parameters for filtering
        therapist_id = request.args.get('therapist_id', type=int)
        status = request.args.get('status')
        scheduled_date = request.args.get('scheduled_date')
        
        db = SessionLocal()
        try:
            query = db.query(PhoneCall)
            
            # Apply filters if provided
            if therapist_id:
                query = query.filter(PhoneCall.therapist_id == therapist_id)
            if status:
                query = query.filter(PhoneCall.status == status)
            if scheduled_date:
                query = query.filter(PhoneCall.scheduled_date == scheduled_date)
            
            # Get results
            phone_calls = query.all()
            return phone_calls
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(phone_call_fields)
    def post(self):
        """Create a new phone call."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('therapist_id', type=int, required=True,
                          help='Therapist ID is required')
        # Optional fields with automatic scheduling
        parser.add_argument('scheduled_date', type=str)
        parser.add_argument('scheduled_time', type=str)
        parser.add_argument('duration_minutes', type=int, default=5)
        parser.add_argument('status', type=str)
        parser.add_argument('notes', type=str)
        parser.add_argument('placement_request_ids', type=list)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Check if we need to find an available slot
            if not args.get('scheduled_date') or not args.get('scheduled_time'):
                slot = find_available_slot(
                    args['therapist_id'],
                    duration_minutes=args.get('duration_minutes', 5)
                )
                
                if not slot:
                    return {
                        'message': 'No available slots found for this therapist'
                    }, 400
                    
                scheduled_date = slot['date']
                scheduled_time = slot['start_time']
            else:
                scheduled_date = args['scheduled_date']
                scheduled_time = args['scheduled_time']
            
            # Create the phone call
            from datetime import datetime
            start_hour, start_minute = map(int, scheduled_time.split(':'))
            from datetime import time
            call_time = time(hour=start_hour, minute=start_minute)
            
            phone_call = PhoneCall(
                therapist_id=args['therapist_id'],
                scheduled_date=scheduled_date,
                scheduled_time=call_time,
                duration_minutes=args.get('duration_minutes', 5),
                notes=args.get('notes'),
                status=args.get('status', PhoneCallStatus.SCHEDULED.value)
            )
            
            db.add(phone_call)
            db.flush()  # Get ID without committing
            
            # Create batches for placement requests if provided
            placement_request_ids = args.get('placement_request_ids', [])
            for pr_id in placement_request_ids:
                batch = PhoneCallBatch(
                    phone_call_id=phone_call.id,
                    placement_request_id=pr_id,
                    priority=1  # Default priority
                )
                db.add(batch)
            
            db.commit()
            db.refresh(phone_call)
            
            return phone_call, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        except Exception as e:
            db.rollback()
            return {'message': f'Error creating phone call: {str(e)}'}, 500
        finally:
            db.close()


class PhoneCallBatchResource(Resource):
    """REST resource for phone call batch operations."""

    @marshal_with(phone_call_batch_fields)
    def get(self, batch_id):
        """Get a specific phone call batch by ID."""
        db = SessionLocal()
        try:
            batch = db.query(PhoneCallBatch).filter(
                PhoneCallBatch.id == batch_id
            ).first()
            if not batch:
                return {'message': 'Phone call batch not found'}, 404
            return batch
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(phone_call_batch_fields)
    def put(self, batch_id):
        """Update an existing phone call batch."""
        parser = reqparse.RequestParser()
        parser.add_argument('discussed', type=bool)
        parser.add_argument('outcome', type=str)
        parser.add_argument('follow_up_required', type=bool)
        parser.add_argument('follow_up_notes', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            batch = db.query(PhoneCallBatch).filter(
                PhoneCallBatch.id == batch_id
            ).first()
            if not batch:
                return {'message': 'Phone call batch not found'}, 404
            
            # Update fields from request
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