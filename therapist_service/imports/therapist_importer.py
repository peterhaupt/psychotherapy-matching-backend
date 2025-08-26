"""Therapist import logic with deduplication and validation."""
import logging
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, date

import requests
from sqlalchemy.exc import SQLAlchemyError

from models.therapist import Therapist, Therapieverfahren
from shared.utils.database import SessionLocal
from shared.config import get_config

logger = logging.getLogger(__name__)


class TherapistImporter:
    """Handle therapist data import with deduplication and validation."""
    
    def __init__(self):
        """Initialize the therapist importer."""
        self.config = get_config()
        self.comm_service_url = self.config.get_service_url('communication', internal=True)
    
    def import_therapist(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Import or update a therapist from JSON data.
        
        Args:
            data: Therapist data from JSON file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Map fields from JSON to our format
            mapped_data = self._map_therapist_data(data)
            
            if not mapped_data:
                return False, "Failed to map therapist data"
            
            # Find existing therapist
            existing = self._find_existing_therapist(mapped_data)
            
            if existing:
                # Update existing therapist
                success, therapist_id, message = self._update_therapist(existing.id, mapped_data)
                if success:
                    return True, f"Therapist updated: ID {therapist_id}"
                else:
                    return False, f"Update failed: {message}"
            else:
                # Create new therapist
                success, therapist_id, message = self._create_therapist(mapped_data)
                if success:
                    return True, f"Therapist created: ID {therapist_id}"
                else:
                    return False, f"Creation failed: {message}"
                    
        except Exception as e:
            logger.error(f"Error importing therapist: {str(e)}", exc_info=True)
            return False, f"Import exception: {str(e)}"
    
    def _map_therapist_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map therapist data from JSON format to our model format.
        
        Args:
            data: Single therapist data from JSON
            
        Returns:
            Mapped data for our model, or None if required fields missing
        """
        try:
            basic_info = data.get('basic_info', {})
            location = data.get('location', {})
            contact = data.get('contact', {})
            
            # Required fields check
            if not all([
                basic_info.get('first_name'),
                basic_info.get('last_name'),
                location.get('postal_code')
            ]):
                logger.warning("Missing required fields in therapist data")
                return None
            
            # Combine street and house number
            street = location.get('street', '')
            house_number = location.get('house_number', '')
            full_street = f"{street} {house_number}".strip() if street else ''
            
            # Map therapy methods to our single enum
            therapy_methods = data.get('therapy_methods', [])
            psychotherapieverfahren = self._map_therapy_methods(therapy_methods)

            # Default salutation to 'Frau' if missing or empty
            salutation = basic_info.get('salutation') or 'Frau'
            
            mapped = {
                # Basic info
                'anrede': salutation,
                'geschlecht': self._map_gender_from_salutation(salutation),
                'titel': basic_info.get('title', ''),
                'vorname': basic_info.get('first_name'),
                'nachname': basic_info.get('last_name'),
                
                # Location
                'strasse': full_street,
                'plz': location.get('postal_code'),
                'ort': location.get('city', ''),
                
                # Contact
                'telefon': contact.get('phone', ''),
                'email': contact.get('email', ''),
                'fax': contact.get('fax', ''),
                
                # Professional info
                'telefonische_erreichbarkeit': data.get('telephone_hours', {}),
                'fremdsprachen': data.get('languages', []),
                'psychotherapieverfahren': psychotherapieverfahren,
                
                # Default values for imported therapists
                'kassensitz': True,
                'status': 'aktiv',
                'potenziell_verfuegbar': False,
                'ueber_curavani_informiert': False,
            }
            
            # Remove empty strings and None values (except for fields that can be empty)
            cleaned = {}
            for key, value in mapped.items():
                if value is not None and value != '':
                    cleaned[key] = value
                elif key in ['titel', 'email', 'fax', 'strasse', 'ort', 'telefon']:
                    # These fields can be empty strings
                    cleaned[key] = value if value is not None else ''
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error mapping therapist data: {str(e)}", exc_info=True)
            return None
    
    def _map_therapy_methods(self, methods: List[str]) -> str:
        """Map therapy methods array to our single enum value.
        
        Based on spec logic:
        - Both types found → 'egal'
        - Only Tiefenpsychologisch → 'tiefenpsychologisch_fundierte_Psychotherapie'
        - Only Verhaltenstherapie → 'Verhaltenstherapie'
        - Default → 'egal'
        """
        has_verhaltenstherapie = any('Verhaltenstherapie' in m for m in methods)
        has_tiefenpsychologisch = any('Tiefenpsychologisch' in m or 'tiefenpsychologisch' in m for m in methods)
        
        if has_verhaltenstherapie and has_tiefenpsychologisch:
            return 'egal'
        elif has_tiefenpsychologisch and not has_verhaltenstherapie:
            return 'tiefenpsychologisch_fundierte_Psychotherapie'
        elif has_verhaltenstherapie and not has_tiefenpsychologisch:
            return 'Verhaltenstherapie'
        else:
            # Default if no recognized methods
            return 'egal'
    
    def _map_gender_from_salutation(self, salutation: str) -> str:
        """Map salutation to gender with German consistency.
        
        Args:
            salutation: Herr/Frau
            
        Returns:
            Gender string for our enum
        """
        if salutation == 'Herr':
            return 'männlich'
        elif salutation == 'Frau':
            return 'weiblich'
        else:
            return 'keine_Angabe'
    
    def _find_existing_therapist(self, data: Dict[str, Any]) -> Optional[Therapist]:
        """Find existing therapist using matching logic.
        
        Primary match: Same first name, last name, and PLZ
        Secondary match: Same first name, PLZ, ort, street, title, and email (if present)
        
        Args:
            data: Mapped therapist data
            
        Returns:
            Existing therapist or None
        """
        db = SessionLocal()
        try:
            # Primary match: same name + PLZ
            existing = db.query(Therapist).filter(
                Therapist.vorname == data.get('vorname'),
                Therapist.nachname == data.get('nachname'),
                Therapist.plz == data.get('plz')
            ).first()
            
            if existing:
                logger.debug(f"Found therapist by primary match: {existing.id}")
                return existing
            
            # Secondary match: marriage name change scenario
            # Same first name, different last name, but same PLZ, ort, street, and title
            # Also check email if present in incoming data
            query = db.query(Therapist).filter(
                Therapist.vorname == data.get('vorname'),
                Therapist.plz == data.get('plz'),
                Therapist.ort == data.get('ort'),
                Therapist.strasse == data.get('strasse'),
                Therapist.titel == data.get('titel', '')  # Exact title match including empty strings
            )
            
            # Add email check if email is present in incoming data
            incoming_email = data.get('email')
            if incoming_email and incoming_email.strip():
                query = query.filter(Therapist.email == incoming_email)
            
            existing = query.first()
            
            if existing:
                logger.info(f"Found therapist by secondary match (possible name change): {existing.id}")
                return existing
            
            return None
            
        finally:
            db.close()
    
    def _create_therapist(self, data: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """Create a new therapist using the API logic.
        
        Args:
            data: Therapist data in our model format
            
        Returns:
            Tuple of (success, therapist_id, error_message)
        """
        from api.therapists import (
            validate_and_get_anrede,
            validate_and_get_geschlecht,
            validate_and_get_therapist_status,
            validate_and_get_therapieverfahren,
            parse_date_field,
            therapist_fields,
            marshal
        )
        
        db = SessionLocal()
        try:
            # Process and validate fields
            processed_data = {}
            
            # Validate enums
            try:
                processed_data['anrede'] = validate_and_get_anrede(data['anrede'])
                processed_data['geschlecht'] = validate_and_get_geschlecht(data['geschlecht'])
                
                if 'status' in data:
                    processed_data['status'] = validate_and_get_therapist_status(data['status'])
                
                if 'psychotherapieverfahren' in data:
                    processed_data['psychotherapieverfahren'] = validate_and_get_therapieverfahren(
                        data['psychotherapieverfahren']
                    )
            except ValueError as e:
                return False, None, str(e)
            
            # Add other fields
            for key, value in data.items():
                if key not in processed_data and value is not None:
                    processed_data[key] = value
            
            # Create therapist
            therapist = Therapist(**processed_data)
            
            db.add(therapist)
            db.commit()
            db.refresh(therapist)
            
            logger.info(f"Created new therapist: {therapist.id}")
            return True, therapist.id, None
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating therapist: {str(e)}")
            return False, None, f"Database error: {str(e)}"
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating therapist: {str(e)}", exc_info=True)
            return False, None, f"Unexpected error: {str(e)}"
        finally:
            db.close()
    
    def _update_therapist(self, therapist_id: int, data: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """Update an existing therapist.
        
        Special rule: Never overwrite existing email with empty value
        
        Args:
            therapist_id: ID of therapist to update
            data: New data for the therapist
            
        Returns:
            Tuple of (success, therapist_id, error_message)
        """
        from api.therapists import (
            validate_and_get_anrede,
            validate_and_get_geschlecht,
            validate_and_get_therapist_status,
            validate_and_get_therapieverfahren,
            parse_date_field,
            therapist_fields,
            marshal
        )
        
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
            if not therapist:
                return False, None, "Therapist not found"
            
            # Track if actual changes were made
            changes_made = False
            
            # Update fields
            for key, value in data.items():
                # Special handling for email - never overwrite with empty
                if key == 'email':
                    if value or not therapist.email:
                        # Only update if new value is not empty OR current email is empty
                        if getattr(therapist, key) != value:
                            setattr(therapist, key, value)
                            changes_made = True
                    # Skip update if new value is empty and we have existing email
                    continue
                
                # Skip fields that shouldn't be updated
                # These are either system fields or manually managed operational fields
                FIELDS_TO_PRESERVE = [
                    'id', 
                    'created_at',
                    # Manual operational fields that should NOT be overwritten by import
                    'status',  # aktiv/gesperrt/inaktiv - manually managed
                    'sperrgrund',  # Reason for blocking
                    'sperrdatum',  # Date of blocking
                    'kassensitz',  # Manually verified/updated
                    'potenziell_verfuegbar',  # Manually set by staff
                    'potenziell_verfuegbar_notizen',  # Manual notes
                    'ueber_curavani_informiert',  # Manually tracked
                    # Inquiry system fields - manually managed
                    'naechster_kontakt_moeglich',
                    'bevorzugte_diagnosen',
                    'alter_min',
                    'alter_max', 
                    'geschlechtspraeferenz',
                    'arbeitszeiten',
                    'bevorzugt_gruppentherapie',
                    # Contact history - managed by communication service
                    'letzter_kontakt_email',
                    'letzter_kontakt_telefon',
                    'letztes_persoenliches_gespraech'
                ]

                if key in FIELDS_TO_PRESERVE:
                    continue
                
                # Validate enum fields
                if key == 'anrede' and value:
                    try:
                        new_value = validate_and_get_anrede(value)
                        if therapist.anrede != new_value:
                            therapist.anrede = new_value
                            changes_made = True
                    except ValueError as e:
                        logger.warning(f"Invalid anrede value: {e}")
                        continue
                        
                elif key == 'geschlecht' and value:
                    try:
                        new_value = validate_and_get_geschlecht(value)
                        if therapist.geschlecht != new_value:
                            therapist.geschlecht = new_value
                            changes_made = True
                    except ValueError as e:
                        logger.warning(f"Invalid geschlecht value: {e}")
                        continue
                        
                elif key == 'status' and value:
                    try:
                        new_value = validate_and_get_therapist_status(value)
                        if therapist.status != new_value:
                            therapist.status = new_value
                            changes_made = True
                    except ValueError as e:
                        logger.warning(f"Invalid status value: {e}")
                        continue
                        
                elif key == 'psychotherapieverfahren' and value:
                    try:
                        new_value = validate_and_get_therapieverfahren(value)
                        if therapist.psychotherapieverfahren != new_value:
                            therapist.psychotherapieverfahren = new_value
                            changes_made = True
                    except ValueError as e:
                        logger.warning(f"Invalid therapieverfahren value: {e}")
                        continue
                
                # Regular fields
                else:
                    current_value = getattr(therapist, key, None)
                    if current_value != value:
                        setattr(therapist, key, value)
                        changes_made = True
            
            if changes_made:
                # Update timestamp
                therapist.updated_at = date.today()
                
                db.commit()
                db.refresh(therapist)
                
                logger.info(f"Updated therapist: {therapist.id}")
            else:
                logger.debug(f"No changes for therapist: {therapist.id}")
            
            return True, therapist.id, None
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating therapist: {str(e)}")
            return False, None, f"Database error: {str(e)}"
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating therapist: {str(e)}", exc_info=True)
            return False, None, f"Unexpected error: {str(e)}"
        finally:
            db.close()
    
    def send_error_notification(self, subject: str, body: str):
        """Send error notification email.
        
        Args:
            subject: Email subject
            body: Email body
        """
        self._send_system_notification(
            subject,
            body,
            sender_name="Therapist Import System"
        )
    
    def _send_system_notification(self, subject: str, body: str, sender_name: str = "Curavani System"):
        """Send system notification via the communication service.
        
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