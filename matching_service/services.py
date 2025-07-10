"""Matching service implementation with template-based email creation."""
import logging
import os
import requests
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from shared.config import get_config

# Get configuration and logger
config = get_config()
logger = logging.getLogger(__name__)


class CommunicationService:
    """Service for handling email and phone call communications."""
    
    @staticmethod
    def _calculate_age(birth_date: str) -> Optional[int]:
        """Calculate age from birth date string.
        
        Args:
            birth_date: Birth date in YYYY-MM-DD format
            
        Returns:
            Age in years or None if birth date is invalid
        """
        if not birth_date:
            return None
            
        try:
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - birth_date_obj.year
            
            # Adjust if birthday hasn't occurred this year
            if today.month < birth_date_obj.month or \
               (today.month == birth_date_obj.month and today.day < birth_date_obj.day):
                age -= 1
                
            return age
        except (ValueError, TypeError):
            logger.warning(f"Invalid birth date format: {birth_date}")
            return None
    
    @staticmethod
    def _format_zeitliche_verfuegbarkeit(verfuegbarkeit: Dict[str, str]) -> str:
        """Format zeitliche verfuegbarkeit from JSONB to readable string.
        
        Args:
            verfuegbarkeit: Dictionary with weekday keys and time range values
            
        Returns:
            Formatted string like "Montag: 09:00 bis 17:00 Uhr, Dienstag: ..."
        """
        if not verfuegbarkeit or not isinstance(verfuegbarkeit, dict):
            return "Nicht angegeben"
        
        # German weekday mapping
        weekday_mapping = {
            'monday': 'Montag',
            'tuesday': 'Dienstag', 
            'wednesday': 'Mittwoch',
            'thursday': 'Donnerstag',
            'friday': 'Freitag',
            'saturday': 'Samstag',
            'sunday': 'Sonntag',
            # Also handle German keys if they exist
            'montag': 'Montag',
            'dienstag': 'Dienstag',
            'mittwoch': 'Mittwoch',
            'donnerstag': 'Donnerstag',
            'freitag': 'Freitag',
            'samstag': 'Samstag',
            'sonntag': 'Sonntag'
        }
        
        formatted_days = []
        
        # Process in weekday order
        weekday_order = ['montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag']
        
        for day_key in weekday_order:
            # Check both English and German keys
            english_key = {
                'montag': 'monday',
                'dienstag': 'tuesday', 
                'mittwoch': 'wednesday',
                'donnerstag': 'thursday',
                'freitag': 'friday',
                'samstag': 'saturday',
                'sonntag': 'sunday'
            }.get(day_key, day_key)
            
            time_range = verfuegbarkeit.get(day_key) or verfuegbarkeit.get(english_key)
            
            if time_range:
                german_day = weekday_mapping.get(day_key, day_key.capitalize())
                
                # Format time range to German format
                if '-' in time_range:
                    start_time, end_time = time_range.split('-', 1)
                    formatted_time = f"{start_time.strip()} bis {end_time.strip()} Uhr"
                else:
                    formatted_time = f"{time_range} Uhr"
                
                formatted_days.append(f"{german_day}: {formatted_time}")
        
        return ', '.join(formatted_days) if formatted_days else "Nicht angegeben"
    
    @staticmethod 
    def create_anfrage_email(
        therapist_id: int,
        patient_data: List[Dict[str, Any]],
        anfrage_id: int
    ) -> Optional[int]:
        """Create an email for a therapist inquiry using templates.
        
        Args:
            therapist_id: ID of the therapist to email
            patient_data: List of patient data dictionaries
            anfrage_id: ID of the inquiry for reference
            
        Returns:
            Email ID if successful, None otherwise
        """
        try:
            # Get therapist data
            therapist = TherapistService.get_therapist(therapist_id)
            if not therapist:
                logger.error(f"Could not fetch therapist {therapist_id} for email creation")
                return None
            
            if not therapist.get('email'):
                logger.error(f"Therapist {therapist_id} has no email address")
                return None
            
            # Set up Jinja2 environment pointing to shared templates
            shared_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared')
            template_dir = os.path.join(shared_path, 'templates', 'emails')
            
            if not os.path.exists(template_dir):
                logger.error(f"Template directory not found: {template_dir}")
                return None
            
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # Process patient data
            processed_patients = []
            for patient in patient_data:
                processed_patient = patient.copy()
                
                # Calculate age
                processed_patient['age'] = CommunicationService._calculate_age(
                    patient.get('geburtsdatum')
                )
                
                # Format zeitliche verfuegbarkeit
                verfuegbarkeit = patient.get('zeitliche_verfuegbarkeit', {})
                processed_patient['zeitliche_verfuegbarkeit_formatted'] = \
                    CommunicationService._format_zeitliche_verfuegbarkeit(verfuegbarkeit)
                
                processed_patients.append(processed_patient)
            
            # Prepare template context
            context = {
                'therapist': therapist,
                'patients': processed_patients,
                'patient_count': len(patient_data),
                'anfrage_id': anfrage_id
            }
            
            # Render template
            template = env.get_template('psychotherapie_anfrage.md')
            email_markdown = template.render(context)
            
            # Prepare email data for communication service
            subject = f"Suche Psychotherapieplätze - Ref: A{anfrage_id}"
            
            url = f"{config.get_service_url('communication', internal=True)}/api/emails"
            email_data = {
                'therapist_id': therapist_id,
                'betreff': subject,
                'inhalt_markdown': email_markdown,
                'empfaenger_email': therapist.get('email'),
                'empfaenger_name': f"{therapist.get('titel', '')} {therapist.get('vorname', '')} {therapist.get('nachname', '')}".strip(),
                'add_legal_footer': True
            }
            
            # Create email via Communication Service
            response = requests.post(url, json=email_data, timeout=10)
            
            if response.status_code in [200, 201]:
                email_result = response.json()
                email_id = email_result.get('id')
                logger.info(f"Created email {email_id} for anfrage {anfrage_id}")
                
                # Queue the email for sending
                update_url = f"{config.get_service_url('communication', internal=True)}/api/emails/{email_id}"
                queue_response = requests.put(
                    update_url, 
                    json={'status': 'In_Warteschlange'},
                    timeout=5
                )
                
                if queue_response.status_code == 200:
                    logger.info(f"Queued email {email_id} for sending")
                else:
                    logger.error(f"Created email {email_id} but failed to queue it: {queue_response.status_code}")
                
                return email_id
            else:
                logger.error(f"Failed to create email: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create email: {str(e)}", exc_info=True)
            return None


class TherapistService:
    """Service for therapist-related operations."""
    
    @staticmethod
    def get_therapist(therapist_id: int) -> Optional[Dict[str, Any]]:
        """Get therapist data by ID.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            Therapist data dictionary or None if not found
        """
        try:
            url = f"{config.get_service_url('therapist', internal=True)}/api/therapists/{therapist_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch therapist {therapist_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching therapist {therapist_id}: {str(e)}")
            return None