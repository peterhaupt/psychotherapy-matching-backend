"""Patient API endpoints implementation with Phase 2 updates - symptom validation and payment fields."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from datetime import datetime, date
import requests
import logging

from models.patient import Patient, Patientenstatus, Therapeutgeschlechtspraeferenz, Anrede, Geschlecht, Therapieverfahren
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from shared.config import get_config
from shared.api.retry_client import RetryAPIClient
# NEW: Import for import status
from imports import ImportStatus

# Get configuration
config = get_config()

# PHASE 2: Valid symptoms list for validation
VALID_SYMPTOMS = [
    # HÄUFIGSTE ANLIEGEN (Top 5)
    "Depression / Niedergeschlagenheit",
    "Ängste / Panikattacken",
    "Burnout / Erschöpfung",
    "Schlafstörungen",
    "Stress / Überforderung",
    # STIMMUNG & GEFÜHLE
    "Trauer / Verlust",
    "Reizbarkeit / Wutausbrüche",
    "Stimmungsschwankungen",
    "Innere Leere",
    "Einsamkeit",
    # DENKEN & GRÜBELN
    "Sorgen / Grübeln",
    "Selbstzweifel",
    "Konzentrationsprobleme",
    "Negative Gedanken",
    "Entscheidungsschwierigkeiten",
    # KÖRPER & GESUNDHEIT
    "Psychosomatische Beschwerden",
    "Chronische Schmerzen",
    "Essstörungen",
    "Suchtprobleme (Alkohol/Drogen)",
    "Sexuelle Probleme",
    # BEZIEHUNGEN & SOZIALES
    "Beziehungsprobleme",
    "Familienkonflikte",
    "Sozialer Rückzug",
    "Mobbing",
    "Trennungsschmerz",
    # BESONDERE BELASTUNGEN
    "Traumatische Erlebnisse",
    "Zwänge",
    "Selbstverletzung",
    "Suizidgedanken",
    "Identitätskrise"
]


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


# Complete output fields definition for patient responses - PHASE 2 UPDATED
patient_fields = {
    'id': fields.Integer,
    # Personal Information
    'anrede': EnumField,
    'geschlecht': EnumField,
    'vorname': fields.String,
    'nachname': fields.String,
    'strasse': fields.String,
    'plz': fields.String,
    'ort': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    # Medical Information - PHASE 2: removed diagnose, symptome is now array
    'hausarzt': fields.String,
    'krankenkasse': fields.String,
    'krankenversicherungsnummer': fields.String,
    'geburtsdatum': DateField,
    # REMOVED: 'diagnose': fields.String,
    'symptome': fields.Raw,  # JSONB array of symptoms
    'erfahrung_mit_psychotherapie': fields.Boolean,
    'letzte_sitzung_vorherige_psychotherapie': DateField,
    # Process Status - PHASE 2: removed psychotherapeutische_sprechstunde
    'vertraege_unterschrieben': fields.Boolean,
    # REMOVED: 'psychotherapeutische_sprechstunde': fields.Boolean,
    'startdatum': DateField,
    'erster_therapieplatz_am': DateField,
    'funktionierender_therapieplatz_am': DateField,
    'status': EnumField,
    'empfehler_der_unterstuetzung': fields.String,
    # Payment Information - PHASE 2: NEW FIELDS
    'zahlungsreferenz': fields.String,
    'zahlung_eingegangen': fields.Boolean,
    # Availability
    'zeitliche_verfuegbarkeit': fields.Raw,
    'raeumliche_verfuegbarkeit': fields.Raw,
    'verkehrsmittel': fields.String,
    # Preferences
    'offen_fuer_gruppentherapie': fields.Boolean,
    'offen_fuer_diga': fields.Boolean,
    'letzter_kontakt': DateField,
    # Therapist Preferences
    'ausgeschlossene_therapeuten': fields.Raw,
    'bevorzugtes_therapeutengeschlecht': EnumField,
    'bevorzugtes_therapieverfahren': EnumField,
    # Timestamps
    'created_at': DateField,
    'updated_at': DateField,
}


def validate_symptoms(symptoms):
    """Validate symptom array according to Phase 2 requirements.
    
    Args:
        symptoms: List of symptom strings
        
    Raises:
        ValueError: If validation fails
    """
    if not symptoms:
        raise ValueError("At least one symptom is required")
    
    if not isinstance(symptoms, list):
        raise ValueError("Symptoms must be provided as an array")
    
    if len(symptoms) < 1 or len(symptoms) > 3:
        raise ValueError("Between 1 and 3 symptoms must be selected")
    
    for symptom in symptoms:
        if symptom not in VALID_SYMPTOMS:
            raise ValueError(f"Invalid symptom: '{symptom}'. Must be from the predefined list")


def validate_and_get_patient_status(status_value: str) -> Patientenstatus:
    """Validate and return Patientenstatus enum.
    
    Args:
        status_value: German status value from request
        
    Returns:
        Patientenstatus enum
        
    Raises:
        ValueError: If status value is invalid
    """
    if not status_value:
        return None
    
    # With German enums, we can directly access by name since name == value
    try:
        return Patientenstatus[status_value]
    except KeyError:
        valid_values = [status.value for status in Patientenstatus]
        raise ValueError(f"Invalid status '{status_value}'. Valid values: {', '.join(valid_values)}")


def validate_and_get_gender_preference(pref_value: str) -> Therapeutgeschlechtspraeferenz:
    """Validate and return Therapeutgeschlechtspraeferenz enum.
    
    Args:
        pref_value: German preference value from request
        
    Returns:
        Therapeutgeschlechtspraeferenz enum or None
        
    Raises:
        ValueError: If preference value is invalid
    """
    if not pref_value:
        return None
    
    try:
        return Therapeutgeschlechtspraeferenz[pref_value]
    except KeyError:
        valid_values = [pref.value for pref in Therapeutgeschlechtspraeferenz]
        raise ValueError(f"Invalid gender preference '{pref_value}'. Valid values: {', '.join(valid_values)}")


def validate_and_get_anrede(anrede_value: str) -> Anrede:
    """Validate and return Anrede enum.
    
    Args:
        anrede_value: German salutation value from request
        
    Returns:
        Anrede enum
        
    Raises:
        ValueError: If anrede value is invalid
    """
    if not anrede_value:
        raise ValueError("Anrede is required")
    
    try:
        return Anrede[anrede_value]
    except KeyError:
        valid_values = [a.value for a in Anrede]
        raise ValueError(f"Invalid anrede '{anrede_value}'. Valid values: {', '.join(valid_values)}")


def validate_and_get_geschlecht(geschlecht_value: str) -> Geschlecht:
    """Validate and return Geschlecht enum.
    
    Args:
        geschlecht_value: German gender value from request
        
    Returns:
        Geschlecht enum
        
    Raises:
        ValueError: If geschlecht value is invalid
    """
    if not geschlecht_value:
        raise ValueError("Geschlecht is required")
    
    try:
        return Geschlecht[geschlecht_value]
    except KeyError:
        valid_values = [g.value for g in Geschlecht]
        raise ValueError(f"Invalid geschlecht '{geschlecht_value}'. Valid values: {', '.join(valid_values)}")


def validate_and_get_therapieverfahren(verfahren_value: str) -> Therapieverfahren:
    """Validate and return Therapieverfahren enum.
    
    Args:
        verfahren_value: German therapy procedure value from request
        
    Returns:
        Therapieverfahren enum or None
        
    Raises:
        ValueError: If therapy procedure value is invalid
    """
    if not verfahren_value:
        return None
    
    try:
        return Therapieverfahren[verfahren_value]
    except KeyError:
        valid_values = [t.value for t in Therapieverfahren]
        raise ValueError(f"Invalid therapy method '{verfahren_value}'. Valid values: {', '.join(valid_values)}")


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


def check_and_apply_payment_status_transition(patient, old_payment_status, db):
    """Check if payment confirmation should trigger automatic status changes.
    
    PHASE 2: Automatic status transition logic
    When zahlung_eingegangen changes from False to True:
    - Set startdatum to today (if vertraege_unterschrieben is true)
    - Change status from "offen" to "auf_der_Suche"
    
    Args:
        patient: The patient object
        old_payment_status: Previous value of zahlung_eingegangen
        db: Database session
    """
    # Check if payment was just confirmed (False -> True)
    if not old_payment_status and patient.zahlung_eingegangen:
        logger = logging.getLogger(__name__)
        logger.info(f"Payment confirmed for patient {patient.id}")
        
        # Check if contracts are signed
        if patient.vertraege_unterschrieben:
            # Set start date if not already set
            if not patient.startdatum:
                patient.startdatum = date.today()
                logger.info(f"Set startdatum to {patient.startdatum} for patient {patient.id}")
            
            # Change status from offen to auf_der_Suche
            if patient.status == Patientenstatus.offen:
                old_status = patient.status
                patient.status = Patientenstatus.auf_der_Suche
                logger.info(f"Changed status from {old_status.value} to {patient.status.value} for patient {patient.id}")


class PatientLastContactResource(Resource):
    """REST resource for updating patient last contact date only."""
    
    def patch(self, patient_id):
        """Update only the last contact date for a patient."""
        parser = reqparse.RequestParser()
        parser.add_argument('date', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"message": "Patient not found"}, 404
            
            # Use provided date or today
            if args.get('date'):
                try:
                    contact_date = datetime.strptime(args.get('date'), '%Y-%m-%d').date()
                except ValueError:
                    return {"message": "Invalid date format. Use YYYY-MM-DD"}, 400
            else:
                contact_date = date.today()
            
            patient.letzter_kontakt = contact_date
            
            db.commit()
            return {
                "message": "Last contact updated", 
                "letzter_kontakt": contact_date.isoformat()
            }, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()


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
        # Personal Information
        parser.add_argument('anrede', type=str)
        parser.add_argument('geschlecht', type=str)
        parser.add_argument('vorname', type=str)
        parser.add_argument('nachname', type=str)
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        # Medical Information - PHASE 2: removed diagnose, symptome is array
        parser.add_argument('hausarzt', type=str)
        parser.add_argument('krankenkasse', type=str)
        parser.add_argument('krankenversicherungsnummer', type=str)
        parser.add_argument('geburtsdatum', type=str)
        # REMOVED: parser.add_argument('diagnose', type=str)
        parser.add_argument('symptome', type=list, location='json')  # PHASE 2: Array of symptoms
        parser.add_argument('erfahrung_mit_psychotherapie', type=bool)
        parser.add_argument('letzte_sitzung_vorherige_psychotherapie', type=str)
        # Process Status - PHASE 2: removed psychotherapeutische_sprechstunde
        parser.add_argument('vertraege_unterschrieben', type=bool)
        # REMOVED: parser.add_argument('psychotherapeutische_sprechstunde', type=bool)
        # Note: startdatum is automatic - will be handled separately
        parser.add_argument('erster_therapieplatz_am', type=str)
        parser.add_argument('funktionierender_therapieplatz_am', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('empfehler_der_unterstuetzung', type=str)
        # Payment Information - PHASE 2: NEW FIELDS
        parser.add_argument('zahlungsreferenz', type=str)
        parser.add_argument('zahlung_eingegangen', type=bool)
        # Availability
        parser.add_argument('zeitliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('raeumliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('verkehrsmittel', type=str)
        # Preferences
        parser.add_argument('offen_fuer_gruppentherapie', type=bool)
        parser.add_argument('offen_fuer_diga', type=bool)
        # Note: letzter_kontakt is automatic - will be ignored
        # Therapist Preferences
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        parser.add_argument('bevorzugtes_therapeutengeschlecht', type=str)
        parser.add_argument('bevorzugtes_therapieverfahren', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
            
            old_status = patient.status
            old_payment_status = patient.zahlung_eingegangen
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    # Skip automatic fields (only letzter_kontakt now)
                    if key in ['letzter_kontakt']:
                        continue
                    
                    if key == 'anrede':
                        try:
                            patient.anrede = validate_and_get_anrede(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'geschlecht':
                        try:
                            patient.geschlecht = validate_and_get_geschlecht(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'symptome':
                        # PHASE 2: Validate symptom array
                        try:
                            validate_symptoms(value)
                            patient.symptome = value
                        except ValueError as e:
                            return {'message': str(e)}, 400
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
                    elif key == 'bevorzugtes_therapieverfahren':
                        try:
                            patient.bevorzugtes_therapieverfahren = validate_and_get_therapieverfahren(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['geburtsdatum', 'erster_therapieplatz_am', 
                                'funktionierender_therapieplatz_am', 'letzte_sitzung_vorherige_psychotherapie']:
                        try:
                            setattr(patient, key, parse_date_field(value, key))
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        setattr(patient, key, value)
            
            # PHASE 2: Check for payment confirmation and apply automatic transitions
            check_and_apply_payment_status_transition(patient, old_payment_status, db)
            
            db.commit()
            db.refresh(patient)
            
            # Return updated patient data
            return marshal(patient, patient_fields)
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, patient_id):
        """Delete patient with cascade to Matching service."""
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"message": "Patient not found"}, 404
            
            # Call Matching service BEFORE deleting patient
            matching_url = config.get_service_url('matching', internal=True)
            cascade_url = f"{matching_url}/api/matching/cascade/patient-deleted"
            
            try:
                response = RetryAPIClient.call_with_retry(
                    method="POST",
                    url=cascade_url,
                    json={"patient_id": patient_id}
                )
                
                if response.status_code != 200:
                    # Matching service couldn't process cascade
                    return {
                        "message": f"Cannot delete patient: Matching service error: {response.text}"
                    }, 500
                    
            except requests.RequestException as e:
                # Network or timeout error after retries
                return {
                    "message": f"Cannot delete patient: Matching service unavailable: {str(e)}"
                }, 503
            
            # Now safe to delete patient
            db.delete(patient)
            db.commit()
            
            return {"message": "Patient deleted successfully"}, 200
            
        except SQLAlchemyError as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()


class PatientListResource(PaginatedListResource):
    """REST resource for patient collection operations."""

    def get(self):
        """Get a list of patients with optional filtering and pagination."""
        # Parse query parameters for filtering
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        
        db = SessionLocal()
        try:
            query = db.query(Patient)
            
            # Apply status filter if provided
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
            
            # Apply search filter if provided
            if search:
                # Create search pattern for case-insensitive partial matching
                search_pattern = f"%{search}%"
                
                # Search across vorname, nachname, and email fields
                search_conditions = or_(
                    Patient.vorname.ilike(search_pattern),
                    Patient.nachname.ilike(search_pattern),
                    Patient.email.ilike(search_pattern)
                )
                
                query = query.filter(search_conditions)
            
            # Use the new helper method
            return self.create_paginated_response(query, marshal, patient_fields)
            
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def post(self):
        """Create a new patient."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('anrede', type=str, required=True,
                           help='Anrede is required')
        parser.add_argument('geschlecht', type=str, required=True,
                           help='Geschlecht is required')
        parser.add_argument('vorname', type=str, required=True,
                           help='Vorname is required')
        parser.add_argument('nachname', type=str, required=True,
                           help='Nachname is required')
        # Optional fields
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('hausarzt', type=str)
        parser.add_argument('krankenkasse', type=str)
        parser.add_argument('krankenversicherungsnummer', type=str)
        parser.add_argument('geburtsdatum', type=str)
        # REMOVED: parser.add_argument('diagnose', type=str)
        parser.add_argument('symptome', type=list, location='json')  # PHASE 2: Array of symptoms
        parser.add_argument('erfahrung_mit_psychotherapie', type=bool)
        parser.add_argument('letzte_sitzung_vorherige_psychotherapie', type=str)
        parser.add_argument('vertraege_unterschrieben', type=bool)
        # REMOVED: parser.add_argument('psychotherapeutische_sprechstunde', type=bool)
        parser.add_argument('erster_therapieplatz_am', type=str)
        parser.add_argument('funktionierender_therapieplatz_am', type=str)
        parser.add_argument('status', type=str)
        parser.add_argument('empfehler_der_unterstuetzung', type=str)
        # Payment Information - PHASE 2: NEW FIELDS
        parser.add_argument('zahlungsreferenz', type=str)
        parser.add_argument('zahlung_eingegangen', type=bool)
        # Availability
        parser.add_argument('zeitliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('raeumliche_verfuegbarkeit', type=dict, location='json')
        parser.add_argument('verkehrsmittel', type=str)
        parser.add_argument('offen_fuer_gruppentherapie', type=bool)
        parser.add_argument('offen_fuer_diga', type=bool)
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        parser.add_argument('bevorzugtes_therapeutengeschlecht', type=str)
        parser.add_argument('bevorzugtes_therapieverfahren', type=str)
        
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
                    # Skip automatic fields (only letzter_kontakt now)
                    if key in ['letzter_kontakt']:
                        continue
                    
                    if key == 'anrede':
                        try:
                            patient_data['anrede'] = validate_and_get_anrede(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'geschlecht':
                        try:
                            patient_data['geschlecht'] = validate_and_get_geschlecht(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'symptome':
                        # PHASE 2: Validate symptom array
                        try:
                            validate_symptoms(value)
                            patient_data['symptome'] = value
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'status':
                        try:
                            patient_data['status'] = validate_and_get_patient_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'bevorzugtes_therapeutengeschlecht':
                        try:
                            patient_data['bevorzugtes_therapeutengeschlecht'] = validate_and_get_gender_preference(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key == 'bevorzugtes_therapieverfahren':
                        try:
                            patient_data['bevorzugtes_therapieverfahren'] = validate_and_get_therapieverfahren(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['geburtsdatum', 'erster_therapieplatz_am', 
                                'funktionierender_therapieplatz_am', 'letzte_sitzung_vorherige_psychotherapie']:
                        try:
                            patient_data[key] = parse_date_field(value, key)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        patient_data[key] = value
            
            patient = Patient(**patient_data)
            
            # PHASE 2: Check if we should set startdatum automatically based on payment
            if patient.vertraege_unterschrieben and patient.zahlung_eingegangen:
                if not patient.startdatum:
                    patient.startdatum = date.today()
                # Also set status if it's still offen
                if patient.status == Patientenstatus.offen:
                    patient.status = Patientenstatus.auf_der_Suche
            
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
            # Return created patient data
            patient_marshalled = marshal(patient, patient_fields)
            
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


class PatientImportStatusResource(Resource):
    """REST resource for patient import status monitoring."""
    
    def get(self):
        """Get the current import status."""
        return ImportStatus.get_status()