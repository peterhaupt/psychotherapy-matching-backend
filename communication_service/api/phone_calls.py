"""Phone call API endpoints implementation with patient support."""
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, time, date, timedelta
import logging

from models.phone_call import PhoneCall, PhoneCallStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from utils.phone_call_scheduler import find_available_slot
# PHASE 2: Import event publishers
from events.producers import publish_phone_call_scheduled, publish_phone_call_completed

# Custom field for nullable foreign keys
class NullableIntegerField(fields.Raw):
    """Field that properly handles nullable integers."""
    def format(self, value):
        """Format the value, returning None for null/0 values."""
        if value is None or value == 0:
            return None
        return value

# Custom field for time formatting
class TimeField(fields.Raw):
    """Field that formats time as HH:MM without seconds."""
    def format(self, value):
        """Format the time value as HH:MM."""
        if value is None:
            return None
        if isinstance(value, time):
            return value.strftime('%H:%M')
        return str(value)

# Output fields definition for phone call responses - German field names
# REMOVED: wiederholen_nach field
phone_call_fields = {
    'id': fields.Integer,
    'therapist_id': NullableIntegerField,  # Use custom field
    'patient_id': NullableIntegerField,    # Use custom field
    'geplantes_datum': fields.String,
    'geplante_zeit': TimeField,  # Use custom time field
    'dauer_minuten': fields.Integer,
    'tatsaechliches_datum': fields.String,
    'tatsaechliche_zeit': TimeField,  # Use custom time field
    'status': fields.String,
    'ergebnis': fields.String,
    'notizen': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
}


class PhoneCallResource(Resource):
    """REST resource for individual phone call operations."""

    def get(self, call_id):
        """Get a specific phone call by ID."""
        db = SessionLocal()
        try:
            phone_call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
            if not phone_call:
                return {'message': 'Phone call not found'}, 404
            return marshal(phone_call, phone_call_fields)
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

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
        # REMOVED: wiederholen_nach argument
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            phone_call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
            if not phone_call:
                return {'message': 'Phone call not found'}, 404
            
            # PHASE 2: Track status changes for events
            old_status = phone_call.status
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        # Make sure the status value is a valid enum value
                        if value not in [e.value for e in PhoneCallStatus]:
                            return {'message': f'Invalid status value: {value}'}, 400
                        phone_call.status = value
                    elif key == 'geplantes_datum' and value:
                        try:
                            phone_call.geplantes_datum = datetime.fromisoformat(value).date()
                        except ValueError:
                            return {'message': f'Invalid date format for geplantes_datum: {value}'}, 400
                    elif key == 'geplante_zeit' and value:
                        try:
                            hour, minute = map(int, value.split(':'))
                            phone_call.geplante_zeit = time(hour=hour, minute=minute)
                        except (ValueError, AttributeError):
                            return {'message': f'Invalid time format for geplante_zeit: {value}'}, 400
                    elif key == 'tatsaechliches_datum' and value:
                        try:
                            phone_call.tatsaechliches_datum = datetime.fromisoformat(value).date()
                        except ValueError:
                            return {'message': f'Invalid date format for tatsaechliches_datum: {value}'}, 400
                    elif key == 'tatsaechliche_zeit' and value:
                        try:
                            hour, minute = map(int, value.split(':'))
                            phone_call.tatsaechliche_zeit = time(hour=hour, minute=minute)
                        except (ValueError, AttributeError):
                            return {'message': f'Invalid time format for tatsaechliche_zeit: {value}'}, 400
                    else:
                        setattr(phone_call, key, value)
            
            db.commit()
            db.refresh(phone_call)
            
            # PHASE 2: Publish event if call was just completed
            if old_status != PhoneCallStatus.abgeschlossen.value and phone_call.status == PhoneCallStatus.abgeschlossen.value:
                call_data_for_event = {
                    'call_id': phone_call.id,
                    'therapist_id': phone_call.therapist_id,
                    'patient_id': phone_call.patient_id,
                    'recipient_type': phone_call.recipient_type,
                    'status': phone_call.status,
                    'ergebnis': phone_call.ergebnis
                }
                
                logging.info(f"Phone call {call_id} completed, publishing event")
                publish_phone_call_completed(
                    phone_call.id, 
                    call_data_for_event,
                    outcome=phone_call.ergebnis
                )
            
            # PHASE 2: Remove direct patient update - this will be handled by event consumer
            # The following code block has been removed:
            # if phone_call.patient_id and phone_call.status == PhoneCallStatus.abgeschlossen.value:
            #     try:
            #         import requests
            #         ... update patient letzter_kontakt directly ...
            
            return marshal(phone_call, phone_call_fields)
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
    """REST resource for phone call collection operations with patient support."""

    def get(self):
        """Get a list of phone calls with optional filtering and pagination."""
        # Parse query parameters for filtering
        therapist_id = request.args.get('therapist_id', type=int)
        patient_id = request.args.get('patient_id', type=int)  # NEW parameter
        recipient_type = request.args.get('recipient_type')  # NEW parameter: 'therapist' or 'patient'
        status = request.args.get('status')
        geplantes_datum = request.args.get('geplantes_datum')
        
        db = SessionLocal()
        try:
            query = db.query(PhoneCall)
            
            # Apply filters based on recipient type
            if recipient_type == 'therapist':
                # Filter for calls to therapists (therapist_id NOT NULL, patient_id NULL)
                query = query.filter(PhoneCall.therapist_id.isnot(None))
                query = query.filter(PhoneCall.patient_id.is_(None))
                if therapist_id:
                    query = query.filter(PhoneCall.therapist_id == therapist_id)
            elif recipient_type == 'patient':
                # Filter for calls to patients (patient_id NOT NULL, therapist_id NULL)
                query = query.filter(PhoneCall.patient_id.isnot(None))
                query = query.filter(PhoneCall.therapist_id.is_(None))
                if patient_id:
                    query = query.filter(PhoneCall.patient_id == patient_id)
            else:
                # No recipient_type specified, use individual filters
                if therapist_id:
                    query = query.filter(PhoneCall.therapist_id == therapist_id)
                if patient_id:
                    query = query.filter(PhoneCall.patient_id == patient_id)
            
            if status:
                query = query.filter(PhoneCall.status == status)
            if geplantes_datum:
                try:
                    date_obj = datetime.fromisoformat(geplantes_datum).date()
                    query = query.filter(PhoneCall.geplantes_datum == date_obj)
                except ValueError:
                    # Invalid date format, return empty result
                    return {
                        "data": [],
                        "page": 1,
                        "limit": self.DEFAULT_LIMIT,
                        "total": 0
                    }
            
            # Order by scheduled date and time (newest first)
            query = query.order_by(PhoneCall.geplantes_datum.desc(), PhoneCall.geplante_zeit.desc())
            
            # Use the new helper method to create paginated response
            return self.create_paginated_response(query, marshal, phone_call_fields)
            
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def post(self):
        """Create a new phone call with support for both therapist and patient recipients."""
        parser = reqparse.RequestParser()
        # Recipient fields - now both optional
        parser.add_argument('therapist_id', type=int, required=False)
        parser.add_argument('patient_id', type=int, required=False)  # NEW field
        
        # Optional fields with automatic scheduling
        parser.add_argument('geplantes_datum', type=str)
        parser.add_argument('geplante_zeit', type=str)
        parser.add_argument('dauer_minuten', type=int, default=5)
        parser.add_argument('status', type=str)
        parser.add_argument('notizen', type=str)
        
        args = parser.parse_args()
        
        # Validate that exactly one recipient type is specified
        if not args.get('therapist_id') and not args.get('patient_id'):
            return {'message': 'Either therapist_id or patient_id is required'}, 400
        if args.get('therapist_id') and args.get('patient_id'):
            return {'message': 'Cannot specify both therapist_id and patient_id'}, 400
        
        db = SessionLocal()
        try:
            # Determine defaults based on recipient type
            if args.get('patient_id'):
                # Default duration for patients is 10 minutes
                if 'dauer_minuten' not in args or args['dauer_minuten'] == 5:
                    args['dauer_minuten'] = 10
            
            # Handle date/time
            if args.get('geplantes_datum'):
                try:
                    scheduled_date = datetime.fromisoformat(args['geplantes_datum']).date()
                except ValueError:
                    return {'message': f'Invalid date format: {args["geplantes_datum"]}'}, 400
            else:
                # Default to tomorrow
                scheduled_date = date.today() + timedelta(days=1)
            
            if args.get('geplante_zeit'):
                scheduled_time = args['geplante_zeit']
            else:
                # Default time based on recipient type
                if args.get('therapist_id'):
                    # For therapists, try to find available slot
                    slot = find_available_slot(
                        args['therapist_id'],
                        start_date=scheduled_date,
                        duration_minutes=args.get('dauer_minuten', 5)
                    )
                    
                    if slot:
                        scheduled_date = datetime.fromisoformat(slot['date']).date()
                        scheduled_time = slot['start_time']
                    else:
                        return {'message': 'No available slots found for this therapist'}, 400
                else:
                    # For patients, default to 10:00
                    scheduled_time = '10:00'
            
            # Create the phone call
            try:
                start_hour, start_minute = map(int, scheduled_time.split(':'))
                call_time = time(hour=start_hour, minute=start_minute)
            except (ValueError, AttributeError):
                return {'message': f'Invalid time format: {scheduled_time}'}, 400
            
            phone_call = PhoneCall(
                therapist_id=args.get('therapist_id'),
                patient_id=args.get('patient_id'),
                geplantes_datum=scheduled_date,
                geplante_zeit=call_time,
                dauer_minuten=args.get('dauer_minuten', 5),
                notizen=args.get('notizen'),
                status=args.get('status', PhoneCallStatus.geplant.value)
            )
            
            db.add(phone_call)
            db.commit()
            db.refresh(phone_call)
            
            # Publish event for phone call creation
            try:
                publish_phone_call_scheduled(phone_call.id, {
                    'therapist_id': phone_call.therapist_id,
                    'patient_id': phone_call.patient_id,
                    'recipient_type': phone_call.recipient_type,
                    'scheduled_date': phone_call.geplantes_datum.isoformat(),
                    'scheduled_time': phone_call.geplante_zeit.isoformat()
                })
            except Exception as e:
                logging.error(f"Error publishing phone_call_scheduled event: {e}")
            
            return marshal(phone_call, phone_call_fields), 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating phone call: {str(e)}", exc_info=True)
            return {'message': f'Error creating phone call: {str(e)}'}, 500
        finally:
            db.close()