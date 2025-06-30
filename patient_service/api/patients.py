"""Patient API endpoints implementation with COMPLETE field exposure and German enum support."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
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


# Custom field for PostgreSQL ARRAY serialization
class ArrayField(fields.Raw):
    """Custom field for PostgreSQL ARRAY serialization."""
    def format(self, value):
        if value is None:
            return []  # Always return empty array instead of null
        # If it's already a list, return as is
        if isinstance(value, list):
            # If the list contains enums, convert them to values
            return [item.value if hasattr(item, 'value') else item for item in value]
        # If it's a single value, wrap in a list
        return [value]


# COMPLETE output fields definition for patient responses - ALL DATABASE FIELDS
patient_fields = {
    'id': fields.Integer,
    
    # Personal Information
    'anrede': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'strasse': fields.String,
    'plz': fields.String,
    'ort': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    
    # Medical Information
    'hausarzt': fields.String,
    'krankenkasse': fields.String,
    'krankenversicherungsnummer': fields.String,
    'geburtsdatum': DateField,
    'diagnose': fields.String,
    
    # NEW Phase 2 Fields
    'symptome': fields.String,
    'erfahrung_mit_psychotherapie': fields.String,
    
    # Process Status
    'vertraege_unterschrieben': fields.Boolean,
    'psychotherapeutische_sprechstunde': fields.Boolean,
    'startdatum': DateField,
    'erster_therapieplatz_am': DateField,
    'funktionierender_therapieplatz_am': DateField,
    'status': EnumField,
    'empfehler_der_unterstuetzung': fields.String,
    
    # Availability
    'zeitliche_verfuegbarkeit': fields.Raw,  # JSONB field
    'raeumliche_verfuegbarkeit': fields.Raw,  # JSONB field
    'verkehrsmittel': fields.String,
    
    # Preferences
    'offen_fuer_gruppentherapie': fields.Boolean,
    'offen_fuer_diga': fields.Boolean,
    'letzter_kontakt': DateField,
    
    # Medical History - PREVIOUSLY MISSING
    'psychotherapieerfahrung': fields.Boolean,
    'stationaere_behandlung': fields.Boolean,
    'berufliche_situation': fields.String,
    'familienstand': fields.String,
    'aktuelle_psychische_beschwerden': fields.String,
    'beschwerden_seit': DateField,
    'bisherige_behandlungen': fields.String,
    'relevante_koerperliche_erkrankungen': fields.String,
    'aktuelle_medikation': fields.String,
    'aktuelle_belastungsfaktoren': fields.String,
    'unterstuetzungssysteme': fields.String,
    
    # Therapy Goals and Expectations - PREVIOUSLY MISSING
    'anlass_fuer_die_therapiesuche': fields.String,
    'erwartungen_an_die_therapie': fields.String,
    'therapieziele': fields.String,
    'fruehere_therapieerfahrungen': fields.String,
    
    # Therapist Exclusions and Preferences
    'ausgeschlossene_therapeuten': fields.Raw,  # JSONB field
    'bevorzugtes_therapeutengeschlecht': EnumField,
    'bevorzugtes_therapieverfahren': ArrayField,  # PostgreSQL ARRAY field
    
    # Timestamps
    'created_at': DateField,
    'updated_at': DateField,
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
        """Update an existing patient - COMPLETE FIELD SUPPORT."""
        parser = reqparse.RequestParser()
        
        # Personal Information
        parser.add_argument('anrede', type=str)
        parser.add_argument('vorname', type=str)
        parser.add_argument('nachname', type=str)
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        
        # Medical Information
        parser.add_argument('hausarzt', type=str)
        parser.add_argument('krankenkasse', type=str)
        parser.add_argument('krankenversicherungsnummer', type=str)
        parser.add_argument('geburtsdatum', type=str)
        parser.add_argument('diagnose', type=str)
        
        # NEW Phase 2 Fields
        parser.add_argument('symptome', type=str)
        parser.add_argument('erfahrung_mit_psychotherapie', type=str)
        
        # Process Status
        parser.add_argument('vertraege_unterschrieben', type=bool)
        parser.add_argument('psychotherapeutische_sprechstunde', type=bool)
        parser.add_argument('startdatum', type=str)
        parser.add_argument('erster_therapieplatz_am', type=str)
        parser.add_argument('funktionierender_therapieplatz_am', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('empfehler_der_unterstuetzung', type=str)
        
        # Availability
        parser.add_argument('zeitliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('raeumliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('verkehrsmittel', type=str)
        
        # Preferences
        parser.add_argument('offen_fuer_gruppentherapie', type=bool)
        parser.add_argument('offen_fuer_diga', type=bool)
        parser.add_argument('letzter_kontakt', type=str)
        
        # Medical History - PREVIOUSLY MISSING
        parser.add_argument('psychotherapieerfahrung', type=bool)
        parser.add_argument('stationaere_behandlung', type=bool)
        parser.add_argument('berufliche_situation', type=str)
        parser.add_argument('familienstand', type=str)
        parser.add_argument('aktuelle_psychische_beschwerden', type=str)
        parser.add_argument('beschwerden_seit', type=str)
        parser.add_argument('bisherige_behandlungen', type=str)
        parser.add_argument('relevante_koerperliche_erkrankungen', type=str)
        parser.add_argument('aktuelle_medikation', type=str)
        parser.add_argument('aktuelle_belastungsfaktoren', type=str)
        parser.add_argument('unterstuetzungssysteme', type=str)
        
        # Therapy Goals and Expectations - PREVIOUSLY MISSING
        parser.add_argument('anlass_fuer_die_therapiesuche', type=str)
        parser.add_argument('erwartungen_an_die_therapie', type=str)
        parser.add_argument('therapieziele', type=str)
        parser.add_argument('fruehere_therapieerfahrungen', type=str)
        
        # Therapist Exclusions and Preferences
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        parser.add_argument('bevorzugtes_therapeutengeschlecht', type=str)
        parser.add_argument('bevorzugtes_therapieverfahren', type=list, location='json')
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    # Skip manual setting of startdatum - PHASE 1 IMPLEMENTATION
                    if key == 'startdatum':
                        continue  # Ignore client-provided startdatum
                    # Skip manual setting of letzter_kontakt - PHASE 2 IMPLEMENTATION
                    elif key == 'letzter_kontakt':
                        continue  # Ignore client-provided letzter_kontakt
                    elif key == 'status':
                        try:
                            patient.status = validate_and_get_patient_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht':
                        try:
                            patient.bevorzugtes_therapeutengeschlecht = validate_and_get_gender_preference(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['geburtsdatum', 'erster_therapieplatz_am', 
                                'funktionierender_therapieplatz_am', 'beschwerden_seit']:
                        try:
                            setattr(patient, key, parse_date_field(value, key))
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        setattr(patient, key, value)
            
            # PHASE 1 IMPLEMENTATION: Check if we need to set startdatum
            if (patient.vertraege_unterschrieben and 
                patient.psychotherapeutische_sprechstunde and 
                patient.startdatum is None):
                patient.startdatum = date.today()
                logging.info(f"Automatically set startdatum for patient {patient_id} to {date.today()}")
            
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
                    # If status value not found, return empty result
                    return {
                        "data": [],
                        "page": 1,
                        "limit": self.DEFAULT_LIMIT,
                        "total": 0
                    }
            
            # Use the new helper method
            return self.create_paginated_response(query, marshal, patient_fields)
            
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def post(self):
        """Create a new patient - COMPLETE FIELD SUPPORT."""
        parser = reqparse.RequestParser()
        
        # Required fields
        parser.add_argument('vorname', type=str, required=True, help='Vorname is required')
        parser.add_argument('nachname', type=str, required=True, help='Nachname is required')
        
        # Personal Information
        parser.add_argument('anrede', type=str)
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        
        # Medical Information
        parser.add_argument('hausarzt', type=str)
        parser.add_argument('krankenkasse', type=str)
        parser.add_argument('krankenversicherungsnummer', type=str)
        parser.add_argument('geburtsdatum', type=str)
        parser.add_argument('diagnose', type=str)
        
        # NEW Phase 2 Fields
        parser.add_argument('symptome', type=str)
        parser.add_argument('erfahrung_mit_psychotherapie', type=str)
        
        # Process Status
        parser.add_argument('vertraege_unterschrieben', type=bool)
        parser.add_argument('psychotherapeutische_sprechstunde', type=bool)
        # PHASE 1 IMPLEMENTATION: Removed startdatum from parser
        # parser.add_argument('startdatum', type=str)  # REMOVED
        parser.add_argument('status', type=str)
        parser.add_argument('empfehler_der_unterstuetzung', type=str)
        
        # Availability
        parser.add_argument('zeitliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('raeumliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('verkehrsmittel', type=str)
        
        # Preferences
        parser.add_argument('offen_fuer_gruppentherapie', type=bool)
        parser.add_argument('offen_fuer_diga', type=bool)
        # PHASE 2 IMPLEMENTATION: Removed letzter_kontakt from parser
        # parser.add_argument('letzter_kontakt', type=str)  # REMOVED
        
        # Medical History - PREVIOUSLY MISSING
        parser.add_argument('psychotherapieerfahrung', type=bool)
        parser.add_argument('stationaere_behandlung', type=bool)
        parser.add_argument('berufliche_situation', type=str)
        parser.add_argument('familienstand', type=str)
        parser.add_argument('aktuelle_psychische_beschwerden', type=str)
        parser.add_argument('beschwerden_seit', type=str)
        parser.add_argument('bisherige_behandlungen', type=str)
        parser.add_argument('relevante_koerperliche_erkrankungen', type=str)
        parser.add_argument('aktuelle_medikation', type=str)
        parser.add_argument('aktuelle_belastungsfaktoren', type=str)
        parser.add_argument('unterstuetzungssysteme', type=str)
        
        # Therapy Goals and Expectations - PREVIOUSLY MISSING
        parser.add_argument('anlass_fuer_die_therapiesuche', type=str)
        parser.add_argument('erwartungen_an_die_therapie', type=str)
        parser.add_argument('therapieziele', type=str)
        parser.add_argument('fruehere_therapieerfahrungen', type=str)
        
        # Therapist Exclusions and Preferences
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        parser.add_argument('bevorzugtes_therapeutengeschlecht', type=str)
        parser.add_argument('bevorzugtes_therapieverfahren', type=list, location='json')
        
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
                    # Skip manual setting of letzter_kontakt - PHASE 2 IMPLEMENTATION
                    if key == 'letzter_kontakt':
                        continue  # Ignore client-provided letzter_kontakt
                    elif key == 'status':
                        try:
                            patient_data['status'] = validate_and_get_patient_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht':
                        try:
                            patient_data[key] = validate_and_get_gender_preference(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['geburtsdatum', 'beschwerden_seit']:
                        try:
                            patient_data[key] = parse_date_field(value, key)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        patient_data[key] = value
            
            patient = Patient(**patient_data)
            
            # PHASE 1 IMPLEMENTATION: Check if we need to set startdatum
            if (patient.vertraege_unterschrieben and 
                patient.psychotherapeutische_sprechstunde):
                patient.startdatum = date.today()
                logging.info(f"Automatically set startdatum for new patient to {date.today()}")
            
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
            # Extract data from paginated response
            emails = []
            if email_response.ok:
                email_result = email_response.json()
                emails = email_result.get('data', []) if isinstance(email_result, dict) else email_result
            
            # Get phone calls
            call_response = requests.get(
                f"{comm_service_url}/api/phone-calls",
                params={'patient_id': patient_id}
            )
            # Extract data from paginated response
            phone_calls = []
            if call_response.ok:
                call_result = call_response.json()
                phone_calls = call_result.get('data', []) if isinstance(call_result, dict) else call_result
            
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