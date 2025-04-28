"""Patient API endpoints implementation."""
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from models.patient import Patient, PatientStatus
from shared.utils.database import SessionLocal
from events.producers import (
    publish_patient_created,
    publish_patient_updated,
    publish_patient_deleted
)


# Output fields definition for patient responses
patient_fields = {
    'id': fields.Integer,
    'anrede': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    'status': fields.String,
    # Add other fields as needed for API responses
}


class PatientResource(Resource):
    """REST resource for individual patient operations."""

    @marshal_with(patient_fields)
    def get(self, patient_id):
        """Get a specific patient by ID."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()  # noqa: E501
            if not patient:
                return {'message': 'Patient not found'}, 404
            return patient
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(patient_fields)
    def put(self, patient_id):
        """Update an existing patient."""
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
            patient = db.query(Patient).filter(
                Patient.id == patient_id
            ).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        # Handle enum conversion
                        patient.status = PatientStatus(value)
                    else:
                        setattr(patient, key, value)
            
            db.commit()
            
            # Publish event for patient update
            patient_data = {
                'vorname': patient.vorname,
                'nachname': patient.nachname,
                'anrede': patient.anrede,
                'email': patient.email,
                'telefon': patient.telefon,
                'status': patient.status.value if patient.status else None
            }
            publish_patient_updated(patient.id, patient_data)
            
            return patient
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, patient_id):
        """Delete a patient."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(
                Patient.id == patient_id
            ).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
            
            db.delete(patient)
            db.commit()
            
            # Publish event for patient deletion
            publish_patient_deleted(patient_id)
            
            return {'message': 'Patient deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class PatientListResource(Resource):
    """REST resource for patient collection operations."""

    @marshal_with(patient_fields)
    def get(self):
        """Get a list of patients with optional filtering."""
        # Parse query parameters for filtering
        status = request.args.get('status')
        
        db = SessionLocal()
        try:
            query = db.query(Patient)
            
            # Apply filters if provided
            if status:
                query = query.filter(Patient.status == PatientStatus(status))
            
            # Get results
            patients = query.all()
            return patients
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(patient_fields)
    def post(self):
        """Create a new patient."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('vorname', type=str, required=True,
                           help='Vorname is required')
        parser.add_argument('nachname', type=str, required=True,
                           help='Nachname is required')
        # Optional fields
        parser.add_argument('anrede', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        # Add other fields as needed
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Create new patient
            patient = Patient(
                vorname=args['vorname'],
                nachname=args['nachname'],
                anrede=args.get('anrede'),
                email=args.get('email'),
                telefon=args.get('telefon'),
                # Add other fields from args
            )
            
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
            # Publish event for patient creation
            patient_data = {
                'vorname': patient.vorname,
                'nachname': patient.nachname,
                'anrede': patient.anrede,
                'email': patient.email,
                'telefon': patient.telefon,
                'status': patient.status.value if patient.status else None
            }
            publish_patient_created(patient.id, patient_data)
            
            return patient, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()