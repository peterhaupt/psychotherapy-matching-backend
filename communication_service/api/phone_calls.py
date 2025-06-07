"""Phone call API endpoints implementation."""
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, time

from models.phone_call import PhoneCall, PhoneCallStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from utils.phone_call_scheduler import find_available_slot

# Output fields definition for phone call responses - German field names
phone_call_fields = {
    'id': fields.Integer,
    'therapist_id': fields.Integer,
    'geplantes_datum': fields.String,
    'geplante_zeit': fields.String,
    'dauer_minuten': fields.Integer,
    'tatsaechliches_datum': fields.String,
    'tatsaechliche_zeit': fields.String,
    'status': fields.String,
    'ergebnis': fields.String,
    'notizen': fields.String,
    'wiederholen_nach': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
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
        parser.add_argument('geplantes_datum', type=str)
        parser.add_argument('geplante_zeit', type=str)
        parser.add_argument('dauer_minuten', type=int)
        parser.add_argument('tatsaechliches_datum', type=str)
        parser.add_argument('tatsaechliche_zeit', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('ergebnis', type=str)
        parser.add_argument('notizen', type=str)
        parser.add_argument('wiederholen_nach', type=str)
        
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
                    elif key == 'geplantes_datum' and value:
                        phone_call.geplantes_datum = datetime.fromisoformat(value).date()
                    elif key == 'geplante_zeit' and value:
                        hour, minute = map(int, value.split(':'))
                        phone_call.geplante_zeit = time(hour=hour, minute=minute)
                    elif key == 'tatsaechliches_datum' and value:
                        phone_call.tatsaechliches_datum = datetime.fromisoformat(value).date()
                    elif key == 'tatsaechliche_zeit' and value:
                        hour, minute = map(int, value.split(':'))
                        phone_call.tatsaechliche_zeit = time(hour=hour, minute=minute)
                    elif key == 'wiederholen_nach' and value:
                        phone_call.wiederholen_nach = datetime.fromisoformat(value).date()
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


class PhoneCallListResource(PaginatedListResource):
    """REST resource for phone call collection operations."""

    @marshal_with(phone_call_fields)
    def get(self):
        """Get a list of phone calls with optional filtering and pagination."""
        # Parse query parameters for filtering
        therapist_id = request.args.get('therapist_id', type=int)
        status = request.args.get('status')
        geplantes_datum = request.args.get('geplantes_datum')
        
        db = SessionLocal()
        try:
            query = db.query(PhoneCall)
            
            # Apply filters if provided
            if therapist_id:
                query = query.filter(PhoneCall.therapist_id == therapist_id)
            if status:
                query = query.filter(PhoneCall.status == status)
            if geplantes_datum:
                query = query.filter(PhoneCall.geplantes_datum == geplantes_datum)
            
            # Apply pagination
            query = self.paginate_query(query)
            
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
        parser.add_argument('geplantes_datum', type=str)
        parser.add_argument('geplante_zeit', type=str)
        parser.add_argument('dauer_minuten', type=int, default=5)
        parser.add_argument('status', type=str)
        parser.add_argument('notizen', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Check if we need to find an available slot
            if not args.get('geplantes_datum') or not args.get('geplante_zeit'):
                slot = find_available_slot(
                    args['therapist_id'],
                    duration_minutes=args.get('dauer_minuten', 5)
                )
                
                if not slot:
                    return {
                        'message': 'No available slots found for this therapist'
                    }, 400
                    
                scheduled_date = slot['date']
                scheduled_time = slot['start_time']
            else:
                scheduled_date = args['geplantes_datum']
                scheduled_time = args['geplante_zeit']
            
            # Create the phone call
            start_hour, start_minute = map(int, scheduled_time.split(':'))
            call_time = time(hour=start_hour, minute=start_minute)
            
            # Parse date if it's a string
            if isinstance(scheduled_date, str):
                scheduled_date = datetime.fromisoformat(scheduled_date).date()
            
            phone_call = PhoneCall(
                therapist_id=args['therapist_id'],
                geplantes_datum=scheduled_date,
                geplante_zeit=call_time,
                dauer_minuten=args.get('dauer_minuten', 5),
                notizen=args.get('notizen'),
                status=args.get('status', PhoneCallStatus.SCHEDULED.value)
            )
            
            db.add(phone_call)
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