"""Patient import logic with validation and duplicate detection."""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

import requests
from sqlalchemy.exc import SQLAlchemyError

from models.patient import Patient
from shared.utils.database import SessionLocal
from shared.config import get_config
from events.producers import publish_patient_created

logger = logging.getLogger(__name__)


class PatientImporter:
    """Handle patient data import with validation and notifications."""
    
    def __init__(self):
        """Initialize the patient importer."""
        self.config = get_config()
        self.comm_service_url = self.config.get_service_url('communication', internal=True)
    
    def import_patient(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Import a patient from JSON data.
        
        Args:
            data: Patient data from JSON file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Extract patient data (ignore metadata and contract texts)
            if 'patient_data' not in data:
                return False, "Missing patient_data section in JSON"
            
            patient_data = data['patient_data']
            
            # Check for duplicate by email
            if 'email' in patient_data and patient_data['email']:
                db = SessionLocal()
                try:
                    existing = db.query(Patient).filter(
                        Patient.email == patient_data['email']
                    ).first()
                    
                    if existing:
                        # Send duplicate notification
                        self._send_duplicate_notification(patient_data, existing)
                        return False, f"Duplicate patient with email: {patient_data['email']}"
                finally:
                    db.close()
            
            # Map fields from JSON to API format
            api_data = self._map_patient_data(patient_data)
            
            # Create patient using API logic
            success, patient_id, error_msg = self._create_patient_via_api(api_data)
            
            if success:
                logger.info(f"Successfully imported patient ID: {patient_id}")
                return True, f"Patient created with ID: {patient_id}"
            else:
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error importing patient: {str(e)}", exc_info=True)
            return False, f"Import exception: {str(e)}"
    
    def _map_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map patient data from JSON format to API format.
        
        Args:
            data: Patient data from JSON
            
        Returns:
            Mapped data for API
        """
        # Direct field mappings
        api_data = {
            'anrede': data.get('anrede'),
            'geschlecht': data.get('geschlecht'),
            'vorname': data.get('vorname'),
            'nachname': data.get('nachname'),
            'strasse': data.get('strasse'),
            'plz': data.get('plz'),
            'ort': data.get('ort'),
            'email': data.get('email'),
            'telefon': data.get('telefon'),
            'hausarzt': data.get('hausarzt'),
            'krankenkasse': data.get('krankenkasse'),
            'geburtsdatum': data.get('geburtsdatum'),
            'symptome': data.get('symptome'),
            'erfahrung_mit_psychotherapie': data.get('erfahrung_mit_psychotherapie'),
            'letzte_sitzung_vorherige_psychotherapie': data.get('letzte_sitzung_vorherige_psychotherapie'),
            'empfehler_der_unterstuetzung': data.get('empfehler_der_unterstuetzung'),
            'verkehrsmittel': data.get('verkehrsmittel'),
            'offen_fuer_gruppentherapie': data.get('offen_fuer_gruppentherapie', False),
            'vertraege_unterschrieben': True,  # Always true for imported patients
        }
        
        # Handle complex fields
        if 'zeitliche_verfuegbarkeit' in data:
            api_data['zeitliche_verfuegbarkeit'] = data['zeitliche_verfuegbarkeit']
        
        if 'raeumliche_verfuegbarkeit' in data:
            api_data['raeumliche_verfuegbarkeit'] = data['raeumliche_verfuegbarkeit']
        
        if 'bevorzugtes_therapeutengeschlecht' in data:
            api_data['bevorzugtes_therapeutengeschlecht'] = data['bevorzugtes_therapeutengeschlecht']
        
        if 'bevorzugtes_therapieverfahren' in data:
            api_data['bevorzugtes_therapieverfahren'] = data['bevorzugtes_therapieverfahren']
        
        # Handle boolean fields from JSON
        if 'hat_ptv11' in data:
            api_data['psychotherapeutische_sprechstunde'] = data['hat_ptv11']
        
        # Remove None values
        api_data = {k: v for k, v in api_data.items() if v is not None}
        
        return api_data
    
    def _create_patient_via_api(self, patient_data: Dict[str, Any]) -> Tuple[bool, int, str]:
        """Create patient using the existing API logic.
        
        Args:
            patient_data: Patient data in API format
            
        Returns:
            Tuple of (success: bool, patient_id: int, error_message: str)
        """
        # Import here to avoid circular imports
        from api.patients import (
            validate_and_get_anrede,
            validate_and_get_geschlecht,
            validate_and_get_patient_status,
            validate_and_get_gender_preference,
            validate_and_get_therapieverfahren,
            parse_date_field,
            patient_fields,
            marshal
        )
        
        db = SessionLocal()
        try:
            # Validate required fields
            if not all(k in patient_data for k in ['anrede', 'geschlecht', 'vorname', 'nachname']):
                return False, None, "Missing required fields"
            
            # Process and validate fields
            processed_data = {}
            
            # Validate enums
            try:
                processed_data['anrede'] = validate_and_get_anrede(patient_data['anrede'])
                processed_data['geschlecht'] = validate_and_get_geschlecht(patient_data['geschlecht'])
            except ValueError as e:
                return False, None, str(e)
            
            # Add other fields
            for key, value in patient_data.items():
                if key in ['anrede', 'geschlecht']:
                    continue  # Already processed
                
                if value is not None:
                    if key == 'status' and value:
                        try:
                            processed_data['status'] = validate_and_get_patient_status(value)
                        except ValueError as e:
                            return False, None, str(e)
                    elif key == 'bevorzugtes_therapeutengeschlecht' and value:
                        try:
                            processed_data['bevorzugtes_therapeutengeschlecht'] = validate_and_get_gender_preference(value)
                        except ValueError as e:
                            return False, None, str(e)
                    elif key == 'bevorzugtes_therapieverfahren' and value:
                        try:
                            processed_data['bevorzugtes_therapieverfahren'] = validate_and_get_therapieverfahren(value)
                        except ValueError as e:
                            return False, None, str(e)
                    elif key in ['geburtsdatum', 'erster_therapieplatz_am', 
                                'funktionierender_therapieplatz_am', 'letzte_sitzung_vorherige_psychotherapie']:
                        try:
                            processed_data[key] = parse_date_field(value, key)
                        except ValueError as e:
                            return False, None, str(e)
                    else:
                        processed_data[key] = value
            
            # Create patient
            patient = Patient(**processed_data)
            
            # Check if we should set startdatum automatically
            if patient.vertraege_unterschrieben and patient.psychotherapeutische_sprechstunde and patient.startdatum is None:
                from datetime import date
                patient.startdatum = date.today()
            
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
            # Publish event
            patient_marshalled = marshal(patient, patient_fields)
            publish_patient_created(patient.id, patient_marshalled)
            
            return True, patient.id, None
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating patient: {str(e)}")
            return False, None, f"Database error: {str(e)}"
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating patient: {str(e)}", exc_info=True)
            return False, None, f"Unexpected error: {str(e)}"
        finally:
            db.close()
    
    def _send_duplicate_notification(self, new_data: Dict[str, Any], existing_patient: Patient):
        """Send email notification about duplicate patient.
        
        Args:
            new_data: Data from the import attempt
            existing_patient: Existing patient record
        """
        subject = f"Duplicate Patient Import Attempt - {new_data.get('email', 'No email')}"
        
        body = f"""
A patient import was attempted but a duplicate email was found.

Import Data:
- Name: {new_data.get('vorname', '')} {new_data.get('nachname', '')}
- Email: {new_data.get('email', '')}
- Date of Birth: {new_data.get('geburtsdatum', '')}

Existing Patient:
- ID: {existing_patient.id}
- Name: {existing_patient.vorname} {existing_patient.nachname}
- Email: {existing_patient.email}
- Created: {existing_patient.created_at}

Please review this case manually.
        """
        
        self._send_system_notification(subject, body, sender_name="Patient Import System")
    
    def send_error_notification(self, subject: str, body: str):
        """Send error notification email.
        
        Args:
            subject: Email subject
            body: Email body
        """
        self._send_system_notification(
            f"Patient Import Error - {subject}",
            body,
            sender_name="Patient Import System"
        )
    
    def _send_system_notification(self, subject: str, body: str, sender_name: str = "Curavani System"):
        """Send system notification via the new system messages endpoint.
        
        Args:
            subject: Email subject
            body: Email body
            sender_name: Name of the sender system
        """
        try:
            notification_data = {
                'subject': subject,
                'message': body,
                'sender_name': sender_name
            }
            
            response = requests.post(
                f"{self.comm_service_url}/api/system-messages",
                json=notification_data
            )
            
            if response.ok:
                result = response.json()
                logger.info(f"System notification sent to {result.get('recipient')}: {subject}")
            else:
                logger.error(f"Failed to send system notification: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending system notification: {str(e)}")
