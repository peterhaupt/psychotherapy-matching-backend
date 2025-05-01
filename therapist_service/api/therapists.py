"""Therapist API endpoints implementation."""
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from models.therapist import Therapist, TherapistStatus
from shared.utils.database import SessionLocal
from events.producers import (
    publish_therapist_created,
    publish_therapist_updated,
    publish_therapist_blocked,
    publish_therapist_unblocked
)


# Output fields definition for therapist responses
therapist_fields = {
    'id': fields.Integer,
    'anrede': fields.String,
    'titel': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    'status': fields.String,
    # Add other fields as needed for API responses
}


class TherapistResource(Resource):
    """REST resource for individual therapist operations."""

    @marshal_with(therapist_fields)
    def get(self, therapist_id):
        """Get a specific therapist by ID."""
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(
                Therapist.id == therapist_id
            ).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            return therapist
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(therapist_fields)
    def put(self, therapist_id):
        """Update an existing therapist."""
        parser = reqparse.RequestParser()
        parser.add_argument('vorname', type=str)
        parser.add_argument('nachname', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('status', type=str)
        # Add other arguments as needed
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(
                Therapist.id == therapist_id
            ).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            
            old_status = therapist.status
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        # Handle enum conversion
                        therapist.status = TherapistStatus(value)
                    else:
                        setattr(therapist, key, value)
            
            db.commit()
            
            # Publish appropriate event based on status change
            therapist_data = {
                'vorname': therapist.vorname,
                'nachname': therapist.nachname,
                'anrede': therapist.anrede,
                'titel': therapist.titel,
                'email': therapist.email,
                'telefon': therapist.telefon,
                'status': therapist.status.value if therapist.status else None
            }
            
            # Check for status changes to publish specific events
            if old_status != therapist.status:
                if therapist.status == TherapistStatus.BLOCKED:
                    publish_therapist_blocked(
                        therapist.id,
                        therapist_data,
                        therapist.sperrgrund
                    )
                elif (old_status == TherapistStatus.BLOCKED and
                      therapist.status == TherapistStatus.ACTIVE):
                    publish_therapist_unblocked(therapist.id, therapist_data)
                else:
                    publish_therapist_updated(therapist.id, therapist_data)
            else:
                publish_therapist_updated(therapist.id, therapist_data)
            
            return therapist
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, therapist_id):
        """Delete a therapist."""
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(
                Therapist.id == therapist_id
            ).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            
            db.delete(therapist)
            db.commit()
            
            return {'message': 'Therapist deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class TherapistListResource(Resource):
    """REST resource for therapist collection operations."""

    @marshal_with(therapist_fields)
    def get(self):
        """Get a list of therapists with optional filtering."""
        # Parse query parameters for filtering
        status = request.args.get('status')
        
        db = SessionLocal()
        try:
            query = db.query(Therapist)
            
            # Apply filters if provided
            if status:
                query = query.filter(Therapist.status == TherapistStatus(status))
            
            # Get results
            therapists = query.all()
            return therapists
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(therapist_fields)
    def post(self):
        """Create a new therapist."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('vorname', type=str, required=True,
                           help='Vorname is required')
        parser.add_argument('nachname', type=str, required=True,
                           help='Nachname is required')
        # Optional fields
        parser.add_argument('anrede', type=str)
        parser.add_argument('titel', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('kassensitz', type=bool)
        # Add other fields as needed
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Create new therapist
            therapist = Therapist(
                vorname=args['vorname'],
                nachname=args['nachname'],
                anrede=args.get('anrede'),
                titel=args.get('titel'),
                email=args.get('email'),
                telefon=args.get('telefon'),
                kassensitz=args.get('kassensitz', True),
                # Add other fields from args
            )
            
            db.add(therapist)
            db.commit()
            db.refresh(therapist)
            
            # Publish event for therapist creation
            therapist_data = {
                'vorname': therapist.vorname,
                'nachname': therapist.nachname,
                'anrede': therapist.anrede,
                'titel': therapist.titel,
                'email': therapist.email,
                'telefon': therapist.telefon,
                'status': therapist.status.value if therapist.status else None
            }
            publish_therapist_created(therapist.id, therapist_data)
            
            return therapist, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()