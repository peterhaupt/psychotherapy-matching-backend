"""Patient API endpoints implementation."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from models.patient import Patient, PatientStatus, TherapistGenderPreference
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from events.producers import (
    publish_patient_created,
    publish_patient_updated,
    publish_patient_deleted
)


# Custom field for enum serialization
class EnumField(fields.Raw):
    """Custom field for enum serialization that returns the enum value."""
    def format(self, value):
        if value is None:
            return None
        # If it's an enum, return its value
        if hasattr(value, 'value'):
            return value.value
        # If it's already a string (e.g., from request), return as is
        return value


# Custom field for date serialization
class DateField(fields.Raw):
    """Custom field for date serialization."""
    def format(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        # Format date as YYYY-MM-DD string
        return value.strftime('%Y-%m-%d')


# Complete output fields definition for patient responses
patient_fields = {
    'id': fields.Integer,
    'anrede': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'strasse': fields.String,
    'plz': fields.String,
    'ort': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    'hausarzt': fields.String,
    'krankenkasse': fields.String,
    'krankenversicherungsnummer': fields.String,
    'geburtsdatum': DateField,
    'diagnose': fields.String,
    'vertraege_unterschrieben': fields.Boolean,
    'psychotherapeutische_sprechstunde': fields.Boolean,
    'startdatum': DateField,
    'erster_therapieplatz_am': DateField,
    'funktionierender_therapieplatz_am': DateField,
    'status': EnumField,
    'empfehler_der_unterstuetzung': fields.String,
    'zeitliche_verfuegbarkeit': fields.Raw,  # JSONB field
    'raeumliche_verfuegbarkeit': fields.Raw,  # JSONB field
    'verkehrsmittel': fields.String,
    'offen_fuer_gruppentherapie': fields.Boolean,
    'offen_fuer_diga': fields.Boolean,
    'ausgeschlossene_therapeuten': fields.Raw,  # JSONB field
    'bevorzugtes_therapeutengeschlecht': EnumField,
    'created_at': DateField,
    'updated_at': DateField,
}


class PatientResource(Resource):
    """REST resource for individual patient operations."""

    def get(self, patient_id):
        """Get a specific patient by ID."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
            return marshal(patient, patient_fields)
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def put(self, patient_id):
        """Update an existing patient."""
        parser = reqparse.RequestParser()
        parser.add_argument('vorname', type=str)
        parser.add_argument('nachname', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('anrede', type=str)
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('hausarzt', type=str)
        parser.add_argument('krankenkasse', type=str)
        parser.add_argument('krankenversicherungsnummer', type=str)
        parser.add_argument('geburtsdatum', type=str)
        parser.add_argument('diagnose', type=str)
        parser.add_argument('vertraege_unterschrieben', type=bool)
        parser.add_argument('psychotherapeutische_sprechstunde', type=bool)
        parser.add_argument('startdatum', type=str)
        parser.add_argument('erster_therapieplatz_am', type=str)
        parser.add_argument('funktionierender_therapieplatz_am', type=str)
        parser.add_argument('empfehler_der_unterstuetzung', type=str)
        parser.add_argument('zeitliche_verfuegbarkeit', type=dict)
        parser.add_argument('raeumliche_verfuegbarkeit', type=dict)
        parser.add_argument('verkehrsmittel', type=str)
        parser.add_argument('offen_fuer_gruppentherapie', type=bool)
        parser.add_argument('offen_fuer_diga', type=bool)
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        parser.add_argument('bevorzugtes_therapeutengeschlecht', type=str)
        
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
                        # Handle status enum - convert German value to enum
                        try:
                            # Find the enum by its value
                            for status in PatientStatus:
                                if status.value == value:
                                    patient.status = status
                                    break
                            else:
                                # If no match found, try by name (for backwards compatibility)
                                patient.status = PatientStatus(value)
                        except ValueError:
                            return {'message': f'Invalid status value: {value}'}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht' and value:
                        # Handle gender preference enum
                        try:
                            patient.bevorzugtes_therapeutengeschlecht = TherapistGenderPreference(value)
                        except ValueError:
                            return {'message': f'Invalid gender preference value: {value}'}, 400
                    elif key in ['geburtsdatum', 'startdatum', 'erster_therapieplatz_am', 'funktionierender_therapieplatz_am'] and value:
                        # Handle date fields
                        try:
                            setattr(patient, key, datetime.strptime(value, '%Y-%m-%d').date())
                        except ValueError:
                            return {'message': f'Invalid date format for {key}. Use YYYY-MM-DD'}, 400
                    else:
                        setattr(patient, key, value)
            
            db.commit()
            db.refresh(patient)
            
            # Publish event for patient update
            patient_data = marshal(patient, patient_fields)
            publish_patient_updated(patient.id, patient_data)
            
            return marshal(patient, patient_fields)
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


class PatientListResource(PaginatedListResource):
    """REST resource for patient collection operations."""

    def get(self):
        """Get a list of patients with optional filtering and pagination."""
        # Parse query parameters for filtering
        status = request.args.get('status')
        
        db = SessionLocal()
        try:
            query = db.query(Patient)
            
            # Apply filters if provided
            if status:
                # Find the enum by its value (German string)
                status_enum = None
                for ps in PatientStatus:
                    if ps.value == status:
                        status_enum = ps
                        break
                
                if status_enum:
                    query = query.filter(Patient.status == status_enum)
                else:
                    # If status value not found, return empty list
                    return []
            
            # Apply pagination
            query = self.paginate_query(query)
            
            # Get results
            patients = query.all()
            
            # Marshal the results
            return [marshal(patient, patient_fields) for patient in patients]
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

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
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('hausarzt', type=str)
        parser.add_argument('krankenkasse', type=str)
        parser.add_argument('krankenversicherungsnummer', type=str)
        parser.add_argument('geburtsdatum', type=str)
        parser.add_argument('diagnose', type=str)
        parser.add_argument('vertraege_unterschrieben', type=bool)
        parser.add_argument('psychotherapeutische_sprechstunde', type=bool)
        parser.add_argument('startdatum', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('empfehler_der_unterstuetzung', type=str)
        parser.add_argument('zeitliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('raeumliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('verkehrsmittel', type=str)
        parser.add_argument('offen_fuer_gruppentherapie', type=bool)
        parser.add_argument('offen_fuer_diga', type=bool)
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        parser.add_argument('bevorzugtes_therapeutengeschlecht', type=str)
        
        try:
            args = parser.parse_args()
        except Exception as e:
            # Format validation errors to match expected format
            if hasattr(e, 'data') and 'message' in e.data:
                # Extract field-specific errors
                errors = []
                for field, msg in e.data['message'].items():
                    errors.append(f"{field}: {msg}")
                return {'message': ' '.join(errors)}, 400
            return {'message': str(e)}, 400
        
        db = SessionLocal()
        try:
            # Create new patient
            patient_data = {}
            
            # Process each argument
            for key, value in args.items():
                if value is not None:
                    if key == 'status' and value:
                        # Handle status enum
                        status_enum = None
                        for ps in PatientStatus:
                            if ps.value == value:
                                status_enum = ps
                                break
                        
                        if status_enum:
                            patient_data['status'] = status_enum
                        else:
                            return {'message': f'Invalid status value: {value}'}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht' and value:
                        # Handle gender preference enum
                        try:
                            patient_data[key] = TherapistGenderPreference(value)
                        except ValueError:
                            return {'message': f'Invalid gender preference value: {value}'}, 400
                    elif key in ['geburtsdatum', 'startdatum'] and value:
                        # Handle date fields
                        try:
                            patient_data[key] = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            return {'message': f'Invalid date format for {key}. Use YYYY-MM-DD'}, 400
                    else:
                        patient_data[key] = value
            
            patient = Patient(**patient_data)
            
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
            # Publish event for patient creation
            patient_marshalled = marshal(patient, patient_fields)
            publish_patient_created(patient.id, patient_marshalled)
            
            return patient_marshalled, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
