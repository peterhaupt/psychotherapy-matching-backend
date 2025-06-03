"""Matching API endpoints implementation."""
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from models.placement_request import PlacementRequest, PlacementRequestStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from events.producers import (
    publish_match_created,
    publish_match_status_changed
)


# Output fields definition for placement request responses
placement_request_fields = {
    'id': fields.Integer,
    'patient_id': fields.Integer,
    'therapist_id': fields.Integer,
    'status': fields.String,
    'created_at': fields.String,
    'email_contact_date': fields.String,
    'phone_contact_date': fields.String,
    'response': fields.String,
    'response_date': fields.String,
    'next_contact_after': fields.String,
    'priority': fields.Integer,
    'notes': fields.String
}


class PlacementRequestResource(Resource):
    """REST resource for individual placement request operations."""

    @marshal_with(placement_request_fields)
    def get(self, request_id):
        """Get a specific placement request by ID."""
        db = SessionLocal()
        try:
            request = db.query(PlacementRequest).filter(
                PlacementRequest.id == request_id
            ).first()
            if not request:
                return {'message': 'Placement request not found'}, 404
            return request
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(placement_request_fields)
    def put(self, request_id):
        """Update an existing placement request."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('response', type=str)
        parser.add_argument('response_date', type=str)
        parser.add_argument('next_contact_after', type=str)
        parser.add_argument('priority', type=int)
        parser.add_argument('notes', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            placement_request = db.query(PlacementRequest).filter(
                PlacementRequest.id == request_id
            ).first()
            if not placement_request:
                return {'message': 'Placement request not found'}, 404
            
            old_status = placement_request.status
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        # Handle enum conversion
                        placement_request.status = PlacementRequestStatus(value)
                    else:
                        setattr(placement_request, key, value)
            
            db.commit()
            
            # Publish event if status changed
            if old_status != placement_request.status:
                publish_match_status_changed(
                    request_id,
                    old_status.value if old_status else None,
                    placement_request.status.value if placement_request.status else None
                )
            
            return placement_request
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, request_id):
        """Delete a placement request."""
        db = SessionLocal()
        try:
            placement_request = db.query(PlacementRequest).filter(
                PlacementRequest.id == request_id
            ).first()
            if not placement_request:
                return {'message': 'Placement request not found'}, 404
            
            db.delete(placement_request)
            db.commit()
            
            return {'message': 'Placement request deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class PlacementRequestListResource(PaginatedListResource):
    """REST resource for placement request collection operations."""

    @marshal_with(placement_request_fields)
    def get(self):
        """Get a list of placement requests with optional filtering and pagination."""
        # Parse query parameters for filtering
        patient_id = request.args.get('patient_id', type=int)
        therapist_id = request.args.get('therapist_id', type=int)
        status = request.args.get('status')
        
        db = SessionLocal()
        try:
            query = db.query(PlacementRequest)
            
            # Apply filters if provided
            if patient_id:
                query = query.filter(PlacementRequest.patient_id == patient_id)
            if therapist_id:
                query = query.filter(PlacementRequest.therapist_id == therapist_id)
            if status:
                query = query.filter(
                    PlacementRequest.status == PlacementRequestStatus(status)
                )
            
            # Apply pagination
            query = self.paginate_query(query)
            
            # Get results
            requests = query.all()
            return requests
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(placement_request_fields)
    def post(self):
        """Create a new placement request."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('patient_id', type=int, required=True,
                          help='Patient ID is required')
        parser.add_argument('therapist_id', type=int, required=True,
                          help='Therapist ID is required')
        # Optional fields
        parser.add_argument('status', type=str)
        parser.add_argument('priority', type=int)
        parser.add_argument('notes', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Create new placement request
            placement_request = PlacementRequest(
                patient_id=args['patient_id'],
                therapist_id=args['therapist_id'],
                priority=args.get('priority', 1),
                notes=args.get('notes')
            )
            
            # Set status if provided, otherwise use default (OPEN)
            if args.get('status'):
                placement_request.status = PlacementRequestStatus(args['status'])
            
            db.add(placement_request)
            db.commit()
            db.refresh(placement_request)
            
            # Publish event for match creation
            publish_match_created(
                placement_request.id,
                placement_request.patient_id,
                placement_request.therapist_id
            )
            
            return placement_request, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()