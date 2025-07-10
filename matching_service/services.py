"""Service layer functions for cross-service operations and business logic."""
import logging
import os
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from jinja2 import Environment, FileSystemLoader

from sqlalchemy.orm import Session

from models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
from models.platzsuche import SuchStatus
from models.therapeutenanfrage import AntwortTyp
from models.therapeut_anfrage_patient import PatientenErgebnis
from shared.config import get_config

# Get configuration and logger
config = get_config()
logger = logging.getLogger(__name__)


class PatientService:
    """Service for interacting with the Patient Service."""
    
    @staticmethod
    def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
        """Fetch patient data from the Patient Service.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Patient data dictionary or None if not found
        """
        try:
            url = f"{config.get_service_url('patient', internal=True)}/api/patients/{patient_id}"
            logger.debug(f"Fetching patient {patient_id} from URL: {url}")
            
            response = requests.get(url, timeout=5)
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Successfully fetched patient {patient_id}")
                return data
            elif response.status_code == 404:
                logger.warning(f"Patient {patient_id} not found")
                return None
            else:
                logger.error(f"Error fetching patient {patient_id}: {response.status_code}")
                logger.error(f"Response body: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch patient {patient_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_patients(patient_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Fetch multiple patients from the Patient Service.
        
        Args:
            patient_ids: List of patient IDs
            
        Returns:
            Dictionary mapping patient ID to patient data
        """
        patients = {}
        for patient_id in patient_ids:
            patient_data = PatientService.get_patient(patient_id)
            if patient_data:
                patients[patient_id] = patient_data
        return patients
    
    @staticmethod
    def get_all_patients(status: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all patients from the Patient Service.
        
        Args:
            status: Optional status filter
            limit: Maximum number of patients to retrieve
            
        Returns:
            List of patient data dictionaries
        """
        try:
            url = f"{config.get_service_url('patient', internal=True)}/api/patients"
            params = {"limit": limit}
            if status:
                params["status"] = status
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Now expecting paginated structure
                return result.get("data", [])
            else:
                logger.error(f"Error fetching patients: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch patients: {str(e)}")
            return []


class TherapistService:
    """Service for interacting with the Therapist Service."""
    
    @staticmethod
    def get_therapist(therapist_id: int) -> Optional[Dict[str, Any]]:
        """Fetch therapist data from the Therapist Service.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            Therapist data dictionary or None if not found
        """
        try:
            url = f"{config.get_service_url('therapist', internal=True)}/api/therapists/{therapist_id}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Therapist {therapist_id} not found")
                return None
            else:
                logger.error(f"Error fetching therapist {therapist_id}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch therapist {therapist_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_all_therapists(status: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all therapists from the Therapist Service.
        
        Args:
            status: Optional status filter (e.g., 'aktiv')
            limit: Maximum number of therapists to retrieve
            
        Returns:
            List of therapist data dictionaries
        """
        try:
            url = f"{config.get_service_url('therapist', internal=True)}/api/therapists"
            params = {"limit": limit}
            if status:
                params["status"] = status
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Now expecting paginated structure
                return result.get("data", [])
            else:
                logger.error(f"Error fetching therapists: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch therapists: {str(e)}")
            return []
    
    @staticmethod
    def get_contactable_therapists() -> List[Dict[str, Any]]:
        """Get all therapists who can be contacted (not in cooling period).
        
        Returns:
            List of therapist data dictionaries
        """
        try:
            url = f"{config.get_service_url('therapist', internal=True)}/api/therapists"
            params = {
                'status': 'aktiv',
                'limit': 1000  # Adjust as needed
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                therapists = result.get("data", [])
                
                # Filter out therapists in cooling period
                today = datetime.utcnow().date()
                contactable = []
                
                for therapist in therapists:
                    next_contact = therapist.get('naechster_kontakt_moeglich')
                    if not next_contact or datetime.fromisoformat(next_contact).date() <= today:
                        contactable.append(therapist)
                
                logger.info(f"Found {len(contactable)} contactable therapists out of {len(therapists)} active")
                return contactable
            else:
                logger.error(f"Error fetching therapists: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch therapists: {str(e)}")
            return []
    
    @staticmethod
    def set_cooling_period(therapist_id: int, weeks: int = 4) -> bool:
        """Set cooling period for a therapist.
        
        Args:
            therapist_id: ID of the therapist
            weeks: Number of weeks for cooling period
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{config.get_service_url('therapist', internal=True)}/api/therapists/{therapist_id}"
            next_contact = datetime.utcnow() + timedelta(weeks=weeks)
            
            data = {
                'naechster_kontakt_moeglich': next_contact.date().isoformat()
            }
            
            response = requests.put(url, json=data, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"Set cooling period for therapist {therapist_id} until {next_contact.date()}")
                return True
            else:
                logger.error(f"Failed to set cooling period for therapist {therapist_id}: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Failed to set cooling period for therapist {therapist_id}: {str(e)}")
            return False


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
    
    @staticmethod
    def schedule_follow_up_call(therapist_id: int, anfrage_id: int) -> Optional[int]:
        """Schedule a follow-up phone call for an anfrage.
        
        Args:
            therapist_id: ID of the therapist
            anfrage_id: ID of the anfrage
            
        Returns:
            Phone call ID if scheduled successfully, None otherwise
        """
        try:
            url = f"{config.get_service_url('communication', internal=True)}/api/phone-calls"
            data = {
                'therapist_id': therapist_id,
                'notizen': f"Follow-up für Anfrage A{anfrage_id}"
            }
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code in [200, 201]:
                call_data = response.json()
                return call_data.get('id')
            else:
                logger.error(f"Failed to schedule phone call: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to schedule phone call: {str(e)}")
            return None
    
    @staticmethod
    def get_emails_for_recipient(
        therapist_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get emails for a specific recipient.
        
        Args:
            therapist_id: ID of the therapist recipient
            patient_id: ID of the patient recipient
            status: Optional status filter
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of email data dictionaries
        """
        try:
            url = f"{config.get_service_url('communication', internal=True)}/api/emails"
            params = {"limit": limit}
            
            if therapist_id:
                params["therapist_id"] = therapist_id
            if patient_id:
                params["patient_id"] = patient_id
            if status:
                params["status"] = status
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Now expecting paginated structure
                return result.get("data", [])
            else:
                logger.error(f"Error fetching emails: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch emails: {str(e)}")
            return []
    
    @staticmethod
    def get_phone_calls_for_recipient(
        therapist_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get phone calls for a specific recipient.
        
        Args:
            therapist_id: ID of the therapist recipient
            patient_id: ID of the patient recipient
            status: Optional status filter
            limit: Maximum number of calls to retrieve
            
        Returns:
            List of phone call data dictionaries
        """
        try:
            url = f"{config.get_service_url('communication', internal=True)}/api/phone-calls"
            params = {"limit": limit}
            
            if therapist_id:
                params["therapist_id"] = therapist_id
            if patient_id:
                params["patient_id"] = patient_id
            if status:
                params["status"] = status
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Now expecting paginated structure
                return result.get("data", [])
            else:
                logger.error(f"Error fetching phone calls: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch phone calls: {str(e)}")
            return []


class GeoCodingService:
    """Service for interacting with the Geocoding Service."""
    
    @staticmethod
    def calculate_distance(
        origin_address: str,
        destination_address: str,
        travel_mode: str = "car"
    ) -> Optional[float]:
        """Calculate distance between two addresses.
        
        Args:
            origin_address: Origin address
            destination_address: Destination address
            travel_mode: Travel mode (car or transit)
            
        Returns:
            Distance in kilometers or None if calculation fails
        """
        try:
            url = f"{config.get_service_url('geocoding', internal=True)}/api/calculate-distance"
            params = {
                'origin': origin_address,
                'destination': destination_address,
                'travel_mode': travel_mode
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('distance_km')
            else:
                logger.error(f"Failed to calculate distance: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to calculate distance: {str(e)}")
            return None


class AnfrageService:
    """Service for anfrage-related operations."""
    
    @staticmethod
    def create_patient_search(db: Session, patient_id: int) -> Platzsuche:
        """Create a new patient search.
        
        Args:
            db: Database session
            patient_id: ID of the patient
            
        Returns:
            Created Platzsuche instance
        """
        search = Platzsuche(
            patient_id=patient_id,
            status=SuchStatus.aktiv,
            ausgeschlossene_therapeuten=[],
            gesamt_angeforderte_kontakte=0
        )
        db.add(search)
        db.commit()
        db.refresh(search)
        
        logger.info(f"Created patient search {search.id} for patient {patient_id}")
        return search
    
    @staticmethod
    def create_anfrage(
        db: Session,
        therapist_id: int,
        patient_searches: List[Tuple[int, int]]
    ) -> Therapeutenanfrage:
        """Create a new anfrage for a therapist.
        
        Args:
            db: Database session
            therapist_id: ID of the therapist
            patient_searches: List of tuples (platzsuche_id, patient_id)
            
        Returns:
            Created Therapeutenanfrage instance
            
        Raises:
            ValueError: If anfrage size is invalid
        """
        anfrage_config = config.get_anfrage_config()
        min_size = anfrage_config['min_size']
        max_size = anfrage_config['max_size']
        
        if len(patient_searches) < min_size or len(patient_searches) > max_size:
            raise ValueError(f"Anfrage must contain between {min_size} and {max_size} patients")
        
        # Create the anfrage
        anfrage = Therapeutenanfrage(
            therapist_id=therapist_id,
            anfragegroesse=len(patient_searches)
        )
        db.add(anfrage)
        db.flush()  # Get the ID without committing
        
        # Add patients to anfrage
        for position, (platzsuche_id, patient_id) in enumerate(patient_searches, 1):
            anfrage_patient = TherapeutAnfragePatient(
                therapeutenanfrage_id=anfrage.id,
                platzsuche_id=platzsuche_id,
                patient_id=patient_id,
                position_in_anfrage=position
            )
            db.add(anfrage_patient)
        
        db.commit()
        db.refresh(anfrage)
        
        logger.info(f"Created anfrage {anfrage.id} for therapist {therapist_id} with {len(patient_searches)} patients")
        return anfrage
    
    @staticmethod
    def send_anfrage(
        db: Session,
        anfrage_id: int
    ) -> bool:
        """Send an anfrage to the therapist via email.
        
        Args:
            db: Database session
            anfrage_id: ID of the anfrage
            
        Returns:
            True if sent successfully, False otherwise
        """
        anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
        if not anfrage:
            logger.error(f"Anfrage {anfrage_id} not found")
            return False
        
        if anfrage.gesendet_datum:
            logger.warning(f"Anfrage {anfrage_id} already sent on {anfrage.gesendet_datum}")
            return False
        
        # Get patient data
        patient_ids = [ap.patient_id for ap in anfrage.anfrage_patients]
        patients = PatientService.get_patients(patient_ids)
        
        if len(patients) != anfrage.anfragegroesse:
            logger.error(f"Could not fetch all patients for anfrage {anfrage_id}")
            return False
        
        # Create patient data list in anfrage order
        patient_data = []
        for ap in anfrage.anfrage_patients:
            if ap.patient_id in patients:
                patient_data.append(patients[ap.patient_id])
        
        # Create and send email
        email_id = CommunicationService.create_anfrage_email(
            anfrage.therapist_id,
            patient_data,
            anfrage.id
        )
        
        if email_id:
            anfrage.mark_as_sent(email_id=email_id)
            db.commit()
            
            logger.info(f"Anfrage {anfrage_id} sent successfully via email {email_id}")
            return True
        else:
            logger.error(f"Failed to send anfrage {anfrage_id}")
            return False
    
    @staticmethod
    def handle_anfrage_response(
        db: Session,
        anfrage_id: int,
        patient_responses: Dict[int, PatientenErgebnis],
        notes: Optional[str] = None
    ) -> None:
        """Handle a therapist's response to an anfrage.
        
        Args:
            db: Database session
            anfrage_id: ID of the anfrage
            patient_responses: Dictionary mapping patient_id to outcome
            notes: Optional notes about the response
        """
        anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
        if not anfrage:
            raise ValueError(f"Anfrage {anfrage_id} not found")
        
        # Update individual patient outcomes
        accepted_count = 0
        rejected_count = 0
        no_response_count = 0
        
        for ap in anfrage.anfrage_patients:
            outcome = patient_responses.get(ap.patient_id)
            if outcome:
                ap.update_outcome(outcome)
                
                if outcome == PatientenErgebnis.angenommen:
                    accepted_count += 1
                elif outcome in [PatientenErgebnis.abgelehnt_Kapazitaet, 
                               PatientenErgebnis.abgelehnt_nicht_geeignet,
                               PatientenErgebnis.abgelehnt_sonstiges]:
                    rejected_count += 1
                    
                    # Add therapist to exclusion list if needed
                    if ap.should_exclude_therapist():
                        search = db.query(Platzsuche).filter_by(id=ap.platzsuche_id).first()
                        if search:
                            search.exclude_therapist(
                                anfrage.therapist_id,
                                reason=f"Rejected: {outcome.value}"
                            )
            else:
                no_response_count += 1
                ap.mark_no_response()
        
        # Update anfrage response
        response_type = anfrage.calculate_response_type()
        anfrage.update_response(
            response_type=response_type,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            no_response_count=no_response_count,
            notes=notes
        )
        
        db.commit()
        logger.info(f"Updated anfrage {anfrage_id} response: {response_type.value}")
    
    @staticmethod
    def check_for_conflicts(db: Session) -> List[Dict[str, Any]]:
        """Check for patients accepted by multiple therapists.
        
        Args:
            db: Database session
            
        Returns:
            List of conflict dictionaries
        """
        # Find all accepted patients
        accepted_entries = db.query(TherapeutAnfragePatient).filter(
            TherapeutAnfragePatient.antwortergebnis == PatientenErgebnis.angenommen
        ).all()
        
        # Group by patient
        patient_acceptances = {}
        for entry in accepted_entries:
            if entry.patient_id not in patient_acceptances:
                patient_acceptances[entry.patient_id] = []
            patient_acceptances[entry.patient_id].append({
                'therapist_id': entry.get_therapist_id(),
                'anfrage_id': entry.therapeutenanfrage_id,
                'response_date': entry.therapeutenanfrage.antwort_datum
            })
        
        # Find conflicts
        conflicts = []
        for patient_id, acceptances in patient_acceptances.items():
            if len(acceptances) > 1:
                # Sort by response date
                acceptances.sort(key=lambda x: x['response_date'] or datetime.min)
                
                conflicts.append({
                    'patient_id': patient_id,
                    'acceptances': acceptances,
                    'winner': acceptances[0]['therapist_id'],
                    'conflict_count': len(acceptances)
                })
        
        return conflicts