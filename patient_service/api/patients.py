"""Patient API endpoints implementation with German enum support and communication history."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import requests
import logging

from models.patient import Patient, PatientStatus, TherapistGenderPreference
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from shared.config import get_config
from events.producers import (
    publish_patient_created,
    publish_patient_updated,
    publish_patient_deleted
)

# Get configuration
config = get_config()

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
    'letzter_kontakt': DateField,  # Last contact date
}


def validate_and_get_patient_status(status_value: str) -> PatientStatus:
    """Validate and return PatientStatus enum.
    
    Args:
        status_value: German status value from request
        
    Returns:
        PatientStatus enum
        
    Raises:
        ValueError: If status value is invalid
    """
    if not status_value:
        return None
    
    # With German enums, we can directly access by name since name == value
    try:
        return PatientStatus[status_value]
    except KeyError:
        valid_values = [status.value for status in PatientStatus]
        raise ValueError(f"Invalid status '{status_value}'. Valid values: {valid_values}")


def validate_and_get_gender_preference(pref_value: str) -> TherapistGenderPreference:
    """Validate and return TherapistGenderPreference enum.
    
    Args:
        pref_value: German preference value from request
        
    Returns:
        TherapistGenderPreference enum
        
    Raises:
        ValueError: If preference value is invalid
    """
    if not pref_value:
        return None
    
    # With German enums, we can directly access by name since name == value
    try:
        return TherapistGenderPreference[pref_value]
    except KeyError:
        valid_values = [pref.value for pref in TherapistGenderPreference]
        raise ValueError(f"Invalid gender preference '{pref_value}'. Valid values: {valid_values}")


def parse_date_field(date_string: str, field_name: str):
    """Parse date string and return date object.
    
    Args:
        date_string: Date in YYYY-MM-DD format
        field_name: Name of field for error messages
        
    Returns:
        date object
        
    Raises:
        ValueError: If date format is invalid
    """
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date format for {field_name}. Use YYYY-MM-DD")


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
        parser.add_argument('letzter_kontakt', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status':
                        try:
                            patient.status = validate_and_get_patient_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht':
                        try:
                            patient.bevorzugtes_therapeutengeschlecht = validate_and_get_gender_preference(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['geburtsdatum', 'startdatum', 'erster_therapieplatz_am', 'funktionierender_therapieplatz_am', 'letzter_kontakt']:
                        try:
                            setattr(patient, key, parse_date_field(value, key))
                        except ValueError as e:
                            return {'message': str(e)}, 400
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
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
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
                try:
                    status_enum = validate_and_get_patient_status(status)
                    query = query.filter(Patient.status == status_enum)
                except ValueError:
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
                    if key == 'status':
                        try:
                            patient_data['status'] = validate_and_get_patient_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht':
                        try:
                            patient_data[key] = validate_and_get_gender_preference(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['geburtsdatum', 'startdatum']:
                        try:
                            patient_data[key] = parse_date_field(value, key)
                        except ValueError as e:
                            return {'message': str(e)}, 400
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


class PatientCommunicationResource(Resource):
    """REST resource for patient communication history."""
    
    def get(self, patient_id):
        """Get communication history for a patient."""
        # Verify patient exists
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
        finally:
            db.close()
        
        # Call communication service to get emails and calls
        comm_service_url = config.get_service_url('communication', internal=True)
        
        try:
            # Get emails
            email_response = requests.get(
                f"{comm_service_url}/api/emails",
                params={'patient_id': patient_id}
            )
            emails = email_response.json() if email_response.ok else []
            
            # Get phone calls
            call_response = requests.get(
                f"{comm_service_url}/api/phone-calls",
                params={'patient_id': patient_id}
            )
            phone_calls = call_response.json() if call_response.ok else []
            
            # Combine and sort by date
            all_communications = []
            
            # Add emails
            for email in emails:
                all_communications.append({
                    'type': 'email',
                    'id': email.get('id'),
                    'date': email.get('gesendet_am') or email.get('created_at'),
                    'subject': email.get('betreff'),
                    'status': email.get('status'),
                    'response_received': email.get('antwort_erhalten'),
                    'data': email
                })
            
            # Add phone calls
            for call in phone_calls:
                all_communications.append({
                    'type': 'phone_call',
                    'id': call.get('id'),
                    'date': f"{call.get('geplantes_datum')} {call.get('geplante_zeit')}",
                    'status': call.get('status'),
                    'outcome': call.get('ergebnis'),
                    'data': call
                })
            
            # Sort by date (newest first)
            all_communications.sort(key=lambda x: x['date'] or '', reverse=True)
            
            return {
                'patient_id': patient_id,
                'patient_name': f"{patient.vorname} {patient.nachname}",
                'last_contact': patient.letzter_kontakt.isoformat() if patient.letzter_kontakt else None,
                'total_emails': len(emails),
                'total_calls': len(phone_calls),
                'communications': all_communications
            }
            
        except Exception as e:
            logging.error(f"Error fetching communication history: {str(e)}")
            return {'message': f'Error fetching communication history: {str(e)}'}, 500