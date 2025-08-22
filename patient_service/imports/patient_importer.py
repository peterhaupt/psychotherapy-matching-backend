"""Patient import logic with validation - Phase 2 updates."""
import logging
import os
from typing import Dict, Any, Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

import requests
from sqlalchemy.exc import SQLAlchemyError

from models.patient import Patient
from shared.utils.database import SessionLocal
from shared.config import get_config

logger = logging.getLogger(__name__)


class PatientImporter:
    """Handle patient data import with validation - Phase 2 updates."""
    
    def __init__(self):
        """Initialize the patient importer."""
        self.config = get_config()
        self.comm_service_url = self.config.get_service_url('communication', internal=True)
    
    def import_patient(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Import a patient from JSON data.
        
        PHASE 2 Updates:
        - Handle symptome as JSONB array
        - Remove diagnosis handling
        - Extract and store zahlungsreferenz
        - Send confirmation email with contract link
        
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
            
            # PHASE 2: Extract zahlungsreferenz from registration_token
            registration_token = data.get('registration_token')
            if registration_token:
                # Take first 8 characters as zahlungsreferenz
                patient_data['zahlungsreferenz'] = registration_token[:8]
            else:
                logger.warning("No registration_token found in import data")
            
            # Map fields from JSON to API format
            api_data = self._map_patient_data(patient_data)
            
            # Create patient using API logic
            success, patient_id, error_msg = self._create_patient_via_api(api_data)
            
            if success:
                logger.info(f"Successfully imported patient ID: {patient_id}")
                
                # PHASE 2: Send confirmation email with contract link
                self._send_patient_confirmation_email(patient_id, api_data)
                
                return True, f"Patient created with ID: {patient_id}"
            else:
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error importing patient: {str(e)}", exc_info=True)
            return False, f"Import exception: {str(e)}"
    
    def _map_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map patient data from JSON format to API format.
        
        PHASE 2 Updates:
        - Remove diagnosis field mapping
        - Ensure symptome is handled as array
        - Remove PTV11/psychotherapeutische_sprechstunde mapping
        - Include zahlungsreferenz if present
        
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
            # PHASE 2: symptome should be an array
            'symptome': data.get('symptome') if isinstance(data.get('symptome'), list) else None,
            'erfahrung_mit_psychotherapie': data.get('erfahrung_mit_psychotherapie'),
            'letzte_sitzung_vorherige_psychotherapie': data.get('letzte_sitzung_vorherige_psychotherapie'),
            'empfehler_der_unterstuetzung': data.get('empfehler_der_unterstuetzung'),
            'verkehrsmittel': data.get('verkehrsmittel'),
            'offen_fuer_gruppentherapie': data.get('offen_fuer_gruppentherapie', False),
            'vertraege_unterschrieben': True,  # Always true for imported patients
            # PHASE 2: Include zahlungsreferenz
            'zahlungsreferenz': data.get('zahlungsreferenz'),
            # PHASE 2: Payment not yet received for new imports
            'zahlung_eingegangen': False,
        }
        
        # REMOVED: diagnosis field mapping
        # REMOVED: hat_ptv11/psychotherapeutische_sprechstunde mapping
        
        # Handle complex fields
        if 'zeitliche_verfuegbarkeit' in data:
            api_data['zeitliche_verfuegbarkeit'] = data['zeitliche_verfuegbarkeit']
        
        if 'raeumliche_verfuegbarkeit' in data:
            api_data['raeumliche_verfuegbarkeit'] = data['raeumliche_verfuegbarkeit']
        
        if 'bevorzugtes_therapeutengeschlecht' in data:
            api_data['bevorzugtes_therapeutengeschlecht'] = data['bevorzugtes_therapeutengeschlecht']
        
        if 'bevorzugtes_therapieverfahren' in data:
            api_data['bevorzugtes_therapieverfahren'] = data['bevorzugtes_therapieverfahren']
        
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
            validate_symptoms,
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
                    if key == 'symptome':
                        # PHASE 2: Validate symptom array
                        try:
                            validate_symptoms(value)
                            processed_data['symptome'] = value
                        except ValueError as e:
                            return False, None, str(e)
                    elif key == 'status' and value:
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
            
            # Note: We don't set startdatum here because zahlung_eingegangen is False
            # The status will remain 'offen' until payment is confirmed
            
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
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
    
    def _send_patient_confirmation_email(self, patient_id: int, patient_data: Dict[str, Any]):
        """Send confirmation email to patient with contract link and payment info.
        
        PHASE 2: Uses template from shared/templates/emails/patient_registration_confirmation.md
        
        Args:
            patient_id: ID of the created patient
            patient_data: Patient data including email and zahlungsreferenz
        """
        try:
            email = patient_data.get('email')
            if not email:
                logger.warning(f"No email address for patient {patient_id}, skipping confirmation email")
                return
            
            # Fetch current prices from web
            try:
                response = requests.get('https://www.curavani.com/prices.json', timeout=10)
                response.raise_for_status()
                prices = response.json()
                
                # Determine price based on therapy type
                offen_fuer_gruppentherapie = patient_data.get('offen_fuer_gruppentherapie', False)
                if offen_fuer_gruppentherapie:
                    price = prices['gruppentherapie']
                    service_type = 'Gruppentherapie'
                else:
                    price = prices['einzeltherapie']
                    service_type = 'Einzeltherapie'
                
                # Format price in German format (e.g., "95,00 Euro")
                formatted_price = f"{price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " Euro"
                
                # Calculate upgrade price difference
                upgrade_diff = prices['einzeltherapie'] - prices['gruppentherapie']
                formatted_upgrade_price = f"{upgrade_diff:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " Euro"
                
            except Exception as e:
                logger.error(f"Failed to fetch prices from web: {str(e)}")
                raise  # Fail the import to retry later
            
            # Set up Jinja2 environment pointing to shared templates
            # In Docker container, shared is mounted at /app/shared
            if os.path.exists('/app/shared'):
                shared_path = '/app/shared'
            else:
                # Local development - go up from patient_service to project root
                shared_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared')
            
            template_dir = os.path.join(shared_path, 'templates', 'emails')
            
            if not os.path.exists(template_dir):
                logger.error(f"Template directory not found: {template_dir}")
                # Fall back to sending without template
                self.send_error_notification(
                    "Email template directory not found",
                    f"Could not find templates at: {template_dir}\nPatient ID: {patient_id}"
                )
                return
            
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # Prepare template context with patient data AND price info
            context = {
                'patient': patient_data,
                'price': formatted_price,
                'price_number': price,
                'service_type': service_type,
                'upgrade_price': formatted_upgrade_price
            }
            
            # Render template
            template = env.get_template('patient_registration_confirmation.md')
            email_markdown = template.render(context)
            
            # Extract subject from first line if it starts with **Betreff:**
            lines = email_markdown.split('\n')
            subject = "Registrierung Suche Psychotherapieplatz erfolgreich"  # Default
            
            if lines and lines[0].startswith('**Betreff:**'):
                subject = lines[0].replace('**Betreff:**', '').strip()
                # Remove subject line from body
                email_markdown = '\n'.join(lines[1:]).strip()
            
            vorname = patient_data.get('vorname', '')
            nachname = patient_data.get('nachname', '')
            
            # Send email via communication service
            email_data = {
                'patient_id': patient_id,
                'betreff': subject,
                'inhalt_markdown': email_markdown,
                'empfaenger_email': email,
                'empfaenger_name': f"{vorname} {nachname}",
                'absender_email': 'info@curavani.com',  # Fixed to .com
                'absender_name': 'Curavani',  # Changed from "Curavani Team"
                'add_legal_footer': True,
                'status': 'In_Warteschlange'  # Queue for sending
            }
            
            response = requests.post(
                f"{self.comm_service_url}/api/emails",
                json=email_data
            )
            
            if response.ok:
                logger.info(f"Confirmation email queued for patient {patient_id}")
            else:
                logger.error(f"Failed to send confirmation email for patient {patient_id}: {response.status_code} - {response.text}")
                # Don't fail the import if email fails - log error and continue
                self.send_error_notification(
                    "Failed to send patient confirmation email",
                    f"Patient ID: {patient_id}\nEmail: {email}\nError: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Error sending confirmation email for patient {patient_id}: {str(e)}")
            # Re-raise to fail the import if it's a price fetching error
            if "Failed to fetch prices" in str(e):
                raise
            # Don't fail the import for other email errors
            self.send_error_notification(
                "Exception sending patient confirmation email",
                f"Patient ID: {patient_id}\nException: {str(e)}"
            )
    
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