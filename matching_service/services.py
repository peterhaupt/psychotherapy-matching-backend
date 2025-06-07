"""Service layer functions for cross-service operations and business logic."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests

from sqlalchemy.orm import Session

from .models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
from .models.platzsuche import SearchStatus
from .models.therapeutenanfrage import ResponseType
from .models.therapeut_anfrage_patient import PatientOutcome
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
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Patient {patient_id} not found")
                return None
            else:
                logger.error(f"Error fetching patient {patient_id}: {response.status_code}")
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
                therapists = response.json()
                # Filter out therapists in cooling period
                today = datetime.utcnow().date()
                contactable = []
                
                for therapist in therapists:
                    next_contact = therapist.get('naechster_kontakt_moeglich')
                    if not next_contact or datetime.fromisoformat(next_contact).date() <= today:
                        contactable.append(therapist)
                
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
    def create_bundle_email(
        therapist_id: int,
        patient_data: List[Dict[str, Any]],
        bundle_id: int
    ) -> Optional[int]:
        """Create an email for a bundle of patients.
        
        Args:
            therapist_id: ID of the therapist
            patient_data: List of patient information dictionaries
            bundle_id: ID of the bundle (for reference in email)
            
        Returns:
            Email ID if created successfully, None otherwise
        """
        try:
            therapist = TherapistService.get_therapist(therapist_id)
            if not therapist:
                return None
            
            # Prepare email content
            subject = f"Therapieanfrage für {len(patient_data)} Patienten"
            
            # Build email body (simplified - in reality would use templates)
            body_html = f"""
            <h2>Neue Therapieanfragen</h2>
            <p>Sehr geehrte/r {therapist.get('anrede', '')} {therapist.get('titel', '')} {therapist.get('nachname', '')},</p>
            <p>wir haben {len(patient_data)} neue Patienten für Sie:</p>
            <ol>
            """
            
            for idx, patient in enumerate(patient_data, 1):
                body_html += f"""
                <li>
                    <strong>{patient.get('vorname')} {patient.get('nachname')}</strong><br>
                    Diagnose: {patient.get('diagnose', 'Nicht angegeben')}<br>
                    Krankenkasse: {patient.get('krankenkasse', 'Nicht angegeben')}
                </li>
                """
            
            body_html += """
            </ol>
            <p>Bitte teilen Sie uns mit, welche Patienten Sie übernehmen können.</p>
            <p>Mit freundlichen Grüßen,<br>Ihr Curavani Team</p>
            """
            
            body_text = f"Neue Therapieanfragen für {len(patient_data)} Patienten..."
            
            # Create email via Communication Service
            url = f"{config.get_service_url('communication', internal=True)}/api/emails"
            data = {
                'therapist_id': therapist_id,
                'betreff': subject,
                'body_html': body_html,
                'body_text': body_text,
                'empfaenger_email': therapist.get('email'),
                'empfaenger_name': f"{therapist.get('vorname')} {therapist.get('nachname')}"
            }
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code in [200, 201]:
                email_data = response.json()
                return email_data.get('id')
            else:
                logger.error(f"Failed to create email: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to create email: {str(e)}")
            return None
    
    @staticmethod
    def schedule_follow_up_call(therapist_id: int, bundle_id: int) -> Optional[int]:
        """Schedule a follow-up phone call for a bundle.
        
        Args:
            therapist_id: ID of the therapist
            bundle_id: ID of the bundle
            
        Returns:
            Phone call ID if scheduled successfully, None otherwise
        """
        try:
            url = f"{config.get_service_url('communication', internal=True)}/api/phone-calls"
            data = {
                'therapist_id': therapist_id,
                'notizen': f"Follow-up für Bündel #{bundle_id}"
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
        patient_address: str,
        therapist_address: str,
        travel_mode: str = "car"
    ) -> Optional[float]:
        """Calculate distance between patient and therapist.
        
        Args:
            patient_address: Patient's address
            therapist_address: Therapist's address
            travel_mode: Travel mode (car or transit)
            
        Returns:
            Distance in kilometers or None if calculation fails
        """
        try:
            url = f"{config.get_service_url('geocoding', internal=True)}/api/calculate-distance"
            params = {
                'origin': patient_address,
                'destination': therapist_address,
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


class BundleService:
    """Service for bundle-related operations."""
    
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
            status=SearchStatus.ACTIVE,
            ausgeschlossene_therapeuten=[],
            gesamt_angeforderte_kontakte=0
        )
        db.add(search)
        db.commit()
        db.refresh(search)
        
        logger.info(f"Created patient search {search.id} for patient {patient_id}")
        return search
    
    @staticmethod
    def create_bundle(
        db: Session,
        therapist_id: int,
        patient_searches: List[Tuple[int, int]]
    ) -> Therapeutenanfrage:
        """Create a new bundle for a therapist.
        
        Args:
            db: Database session
            therapist_id: ID of the therapist
            patient_searches: List of tuples (platzsuche_id, patient_id)
            
        Returns:
            Created Therapeutenanfrage instance
            
        Raises:
            ValueError: If bundle size is invalid
        """
        if len(patient_searches) < 3 or len(patient_searches) > 6:
            raise ValueError("Bundle must contain between 3 and 6 patients")
        
        # Create the bundle
        bundle = Therapeutenanfrage(
            therapist_id=therapist_id,
            buendelgroesse=len(patient_searches)
        )
        db.add(bundle)
        db.flush()  # Get the ID without committing
        
        # Add patients to bundle
        for position, (platzsuche_id, patient_id) in enumerate(patient_searches, 1):
            bundle_patient = TherapeutAnfragePatient(
                therapeutenanfrage_id=bundle.id,
                platzsuche_id=platzsuche_id,
                patient_id=patient_id,
                position_im_buendel=position
            )
            db.add(bundle_patient)
        
        db.commit()
        db.refresh(bundle)
        
        logger.info(f"Created bundle {bundle.id} for therapist {therapist_id} with {len(patient_searches)} patients")
        return bundle
    
    @staticmethod
    def send_bundle(
        db: Session,
        bundle_id: int
    ) -> bool:
        """Send a bundle to the therapist via email.
        
        Args:
            db: Database session
            bundle_id: ID of the bundle
            
        Returns:
            True if sent successfully, False otherwise
        """
        bundle = db.query(Therapeutenanfrage).filter_by(id=bundle_id).first()
        if not bundle:
            logger.error(f"Bundle {bundle_id} not found")
            return False
        
        # Get patient data
        patient_ids = [bp.patient_id for bp in bundle.bundle_patients]
        patients = PatientService.get_patients(patient_ids)
        
        if len(patients) != bundle.buendelgroesse:
            logger.error(f"Could not fetch all patients for bundle {bundle_id}")
            return False
        
        # Create patient data list in bundle order
        patient_data = []
        for bp in bundle.bundle_patients:
            if bp.patient_id in patients:
                patient_data.append(patients[bp.patient_id])
        
        # Create and send email
        email_id = CommunicationService.create_bundle_email(
            bundle.therapist_id,
            patient_data,
            bundle.id
        )
        
        if email_id:
            bundle.mark_as_sent(email_id=email_id)
            db.commit()
            
            # Set cooling period for therapist
            TherapistService.set_cooling_period(bundle.therapist_id)
            
            logger.info(f"Bundle {bundle_id} sent successfully via email {email_id}")
            return True
        else:
            logger.error(f"Failed to send bundle {bundle_id}")
            return False
    
    @staticmethod
    def handle_bundle_response(
        db: Session,
        bundle_id: int,
        patient_responses: Dict[int, PatientOutcome],
        notes: Optional[str] = None
    ) -> None:
        """Handle a therapist's response to a bundle.
        
        Args:
            db: Database session
            bundle_id: ID of the bundle
            patient_responses: Dictionary mapping patient_id to outcome
            notes: Optional notes about the response
        """
        bundle = db.query(Therapeutenanfrage).filter_by(id=bundle_id).first()
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")
        
        # Update individual patient outcomes
        accepted_count = 0
        rejected_count = 0
        no_response_count = 0
        
        for bp in bundle.bundle_patients:
            outcome = patient_responses.get(bp.patient_id)
            if outcome:
                bp.update_outcome(outcome)
                
                if outcome == PatientOutcome.ACCEPTED:
                    accepted_count += 1
                elif outcome in [PatientOutcome.REJECTED_CAPACITY, 
                               PatientOutcome.REJECTED_NOT_SUITABLE,
                               PatientOutcome.REJECTED_OTHER]:
                    rejected_count += 1
                    
                    # Add therapist to exclusion list if needed
                    if bp.should_exclude_therapist():
                        search = db.query(Platzsuche).filter_by(id=bp.platzsuche_id).first()
                        if search:
                            search.exclude_therapist(
                                bundle.therapist_id,
                                reason=f"Rejected: {outcome.value}"
                            )
            else:
                no_response_count += 1
        
        # Update bundle response
        response_type = bundle.calculate_response_type()
        bundle.update_response(
            response_type=response_type,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            no_response_count=no_response_count,
            notes=notes
        )
        
        db.commit()
        logger.info(f"Updated bundle {bundle_id} response: {response_type.value}")