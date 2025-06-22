"""Service layer functions for cross-service operations and business logic."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests

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
    @staticmethod
    def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
        try:
            url = f"{config.get_service_url('patient', internal=True)}/api/patients/{patient_id}"
            logger.info(f"Fetching patient {patient_id} from URL: {url}")  # ADD THIS
            
            response = requests.get(url, timeout=5)
            logger.info(f"Response status: {response.status_code}")  # ADD THIS
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched patient {patient_id}")  # ADD THIS
                return data
            elif response.status_code == 404:
                logger.warning(f"Patient {patient_id} not found")
                return None
            else:
                logger.error(f"Error fetching patient {patient_id}: {response.status_code}")
                logger.error(f"Response body: {response.text}")  # ADD THIS
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch patient {patient_id}: {str(e)}")
            logger.error(f"URL was: {url}")  # ADD THIS
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
                data = response.json()
                return data.get("data", [])
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
                data = response.json()
                return data.get("data", [])
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
                data = response.json()
                therapists = data.get("data", [])
                
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
    """Service for interacting with the Communication Service."""
    
    @staticmethod
    def create_anfrage_email(
        therapist_id: int,
        patient_data: List[Dict[str, Any]],
        anfrage_id: int
    ) -> Optional[int]:
        """Create an email for an anfrage of patients.
        
        Args:
            therapist_id: ID of the therapist
            patient_data: List of patient information dictionaries
            anfrage_id: ID of the anfrage (for reference in email)
            
        Returns:
            Email ID if created successfully, None otherwise
        """
        try:
            therapist = TherapistService.get_therapist(therapist_id)
            if not therapist:
                logger.error(f"Could not fetch therapist {therapist_id} for email creation")
                return None
            
            # Check if therapist has email
            if not therapist.get('email'):
                logger.error(f"Therapist {therapist_id} has no email address")
                return None
            
            # Prepare email content
            subject = f"Therapieanfrage für {len(patient_data)} Patienten"
            
            # Build email body
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c5aa0;">Neue Therapieanfragen</h2>
                <p>Sehr geehrte/r {therapist.get('anrede', '')} {therapist.get('titel', '')} {therapist.get('nachname', '')},</p>
                <p>wir haben {len(patient_data)} neue Therapieanfragen für Sie:</p>
                
                <ol style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
            """
            
            body_text = f"Neue Therapieanfragen\n\n"
            body_text += f"Sehr geehrte/r {therapist.get('anrede', '')} {therapist.get('titel', '')} {therapist.get('nachname', '')},\n\n"
            body_text += f"wir haben {len(patient_data)} neue Therapieanfragen für Sie:\n\n"
            
            for idx, patient in enumerate(patient_data, 1):
                # HTML version
                body_html += f"""
                <li style="margin-bottom: 15px;">
                    <strong>{patient.get('vorname', '')} {patient.get('nachname', '')}</strong><br>
                    <span style="color: #666;">
                        Alter: {CommunicationService._calculate_age(patient.get('geburtsdatum'))} Jahre<br>
                        Diagnose: {patient.get('diagnose', 'Nicht angegeben')}<br>
                        Krankenkasse: {patient.get('krankenkasse', 'Nicht angegeben')}<br>
                        PLZ/Ort: {patient.get('plz', '')} {patient.get('ort', '')}
                    </span>
                </li>
                """
                
                # Text version
                body_text += f"{idx}. {patient.get('vorname', '')} {patient.get('nachname', '')}\n"
                body_text += f"   Alter: {CommunicationService._calculate_age(patient.get('geburtsdatum'))} Jahre\n"
                body_text += f"   Diagnose: {patient.get('diagnose', 'Nicht angegeben')}\n"
                body_text += f"   Krankenkasse: {patient.get('krankenkasse', 'Nicht angegeben')}\n"
                body_text += f"   PLZ/Ort: {patient.get('plz', '')} {patient.get('ort', '')}\n\n"
            
            body_html += """
                </ol>
                <p>Bitte teilen Sie uns mit, welche Patienten Sie übernehmen können. Sie können uns einfach auf diese E-Mail antworten.</p>
                <p style="color: #666; font-size: 0.9em;">
                    Referenz-Nr: A{anfrage_id}<br>
                    Diese Anfrage wurde automatisch generiert.
                </p>
                <p>Mit freundlichen Grüßen,<br>
                <strong>Ihr Curavani Team</strong></p>
            </body>
            </html>
            """.format(anfrage_id=anfrage_id)
            
            body_text += f"\nBitte teilen Sie uns mit, welche Patienten Sie übernehmen können.\n"
            body_text += f"Sie können uns einfach auf diese E-Mail antworten.\n\n"
            body_text += f"Referenz-Nr: A{anfrage_id}\n\n"
            body_text += "Mit freundlichen Grüßen,\nIhr Curavani Team"
            
            # Create email via Communication Service
            url = f"{config.get_service_url('communication', internal=True)}/api/emails"
            data = {
                'therapist_id': therapist_id,
                'betreff': subject,
                'body_html': body_html,
                'body_text': body_text,
                'empfaenger_email': therapist.get('email'),
                'empfaenger_name': f"{therapist.get('vorname', '')} {therapist.get('nachname', '')}"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                email_data = response.json()
                email_id = email_data.get('id')
                logger.info(f"Created email {email_id} for anfrage {anfrage_id}")
                return email_id
            else:
                logger.error(f"Failed to create email: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to create email: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_age(birthdate_str: Optional[str]) -> str:
        """Calculate age from birthdate string.
        
        Args:
            birthdate_str: Birthdate in ISO format
            
        Returns:
            Age as string or "Unbekannt" if cannot calculate
        """
        if not birthdate_str:
            return "Unbekannt"
        
        try:
            birthdate = datetime.fromisoformat(birthdate_str).date()
            today = datetime.utcnow().date()
            age = today.year - birthdate.year
            
            # Adjust if birthday hasn't occurred this year
            if (today.month, today.day) < (birthdate.month, birthdate.day):
                age -= 1
            
            return str(age)
        except (ValueError, TypeError):
            return "Unbekannt"
    
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