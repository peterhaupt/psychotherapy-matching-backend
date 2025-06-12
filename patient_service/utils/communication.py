"""Helper functions for patient communication."""
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from shared.config import get_config
from models.patient import Patient
from shared.utils.database import SessionLocal

# Get configuration
config = get_config()
logger = logging.getLogger(__name__)


def send_patient_email(
    patient_id: int, 
    subject: str, 
    body_html: str, 
    body_text: str,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None
) -> bool:
    """Send an email to a patient via the communication service.
    
    Args:
        patient_id: ID of the patient to email
        subject: Email subject line
        body_html: HTML content of the email
        body_text: Plain text content of the email
        template_name: Optional template name for standardized emails
        template_context: Optional context for template rendering
        
    Returns:
        bool: True if email was created successfully, False otherwise
    """
    db = SessionLocal()
    try:
        # Get patient data
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            logger.error(f"Patient {patient_id} not found")
            return False
            
        if not patient.email:
            logger.warning(f"Patient {patient_id} has no email address")
            return False
        
        # Update last contact date
        patient.letzter_kontakt = datetime.utcnow().date()
        db.commit()
        
        # Send via communication service
        comm_url = config.get_service_url('communication', internal=True)
        
        # If template is provided, render it
        if template_name and template_context:
            # Add patient data to template context
            template_context.update({
                'patient': {
                    'vorname': patient.vorname,
                    'nachname': patient.nachname,
                    'anrede': patient.anrede or '',
                    'email': patient.email
                }
            })
            # Note: Template rendering would be done by communication service
            # For now, we just use the provided HTML/text
        
        # Create email request
        email_data = {
            'patient_id': patient_id,
            'betreff': subject,
            'inhalt_html': body_html,
            'inhalt_text': body_text,
            'empfaenger_email': patient.email,
            'empfaenger_name': f"{patient.vorname} {patient.nachname}"
        }
        
        response = requests.post(
            f"{comm_url}/api/emails",
            json=email_data
        )
        
        if response.ok:
            logger.info(f"Email created successfully for patient {patient_id}")
            return True
        else:
            logger.error(f"Failed to create email for patient {patient_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email to patient {patient_id}: {str(e)}")
        return False
    finally:
        db.close()


def schedule_patient_call(
    patient_id: int, 
    notes: str,
    scheduled_date: Optional[str] = None,
    scheduled_time: Optional[str] = None,
    duration_minutes: int = 10
) -> Optional[int]:
    """Schedule a phone call with a patient.
    
    Args:
        patient_id: ID of the patient to call
        notes: Notes about the purpose of the call
        scheduled_date: Date for the call (YYYY-MM-DD format), defaults to tomorrow
        scheduled_time: Time for the call (HH:MM format), defaults to 10:00
        duration_minutes: Duration of the call in minutes (default: 10)
        
    Returns:
        int: ID of the created phone call, or None if failed
    """
    db = SessionLocal()
    try:
        # Get patient data
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            logger.error(f"Patient {patient_id} not found")
            return None
            
        if not patient.telefon:
            logger.warning(f"Patient {patient_id} has no phone number")
            return None
        
        # Send via communication service
        comm_url = config.get_service_url('communication', internal=True)
        
        # Create phone call request
        call_data = {
            'patient_id': patient_id,
            'notizen': notes,
            'dauer_minuten': duration_minutes
        }
        
        # Add date/time if provided
        if scheduled_date:
            call_data['geplantes_datum'] = scheduled_date
        if scheduled_time:
            call_data['geplante_zeit'] = scheduled_time
        
        response = requests.post(
            f"{comm_url}/api/phone-calls",
            json=call_data
        )
        
        if response.ok:
            call_id = response.json().get('id')
            logger.info(f"Phone call {call_id} scheduled for patient {patient_id}")
            return call_id
        else:
            logger.error(f"Failed to schedule call for patient {patient_id}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error scheduling call for patient {patient_id}: {str(e)}")
        return None
    finally:
        db.close()


def send_welcome_email(patient_id: int) -> bool:
    """Send a welcome email to a newly registered patient.
    
    Args:
        patient_id: ID of the patient
        
    Returns:
        bool: True if email was sent successfully
    """
    subject = "Willkommen bei der Therapieplatz-Vermittlung"
    
    body_html = """
    <p>Sehr geehrte/r Patient/in,</p>
    
    <p>herzlich willkommen bei unserer Therapieplatz-Vermittlung. Wir freuen uns, 
    Sie bei der Suche nach einem passenden Therapieplatz unterstützen zu können.</p>
    
    <p><strong>Die nächsten Schritte:</strong></p>
    <ul>
        <li>Wir beginnen umgehend mit der Suche nach passenden Therapeuten</li>
        <li>Sie werden regelmäßig über den Fortschritt informiert</li>
        <li>Bei Fragen stehen wir Ihnen jederzeit zur Verfügung</li>
    </ul>
    
    <p>Mit freundlichen Grüßen,<br>
    Ihr Therapieplatz-Vermittlungsteam</p>
    """
    
    body_text = """
    Sehr geehrte/r Patient/in,
    
    herzlich willkommen bei unserer Therapieplatz-Vermittlung. Wir freuen uns, 
    Sie bei der Suche nach einem passenden Therapieplatz unterstützen zu können.
    
    Die nächsten Schritte:
    - Wir beginnen umgehend mit der Suche nach passenden Therapeuten
    - Sie werden regelmäßig über den Fortschritt informiert
    - Bei Fragen stehen wir Ihnen jederzeit zur Verfügung
    
    Mit freundlichen Grüßen,
    Ihr Therapieplatz-Vermittlungsteam
    """
    
    return send_patient_email(patient_id, subject, body_html, body_text)


def send_status_update_email(
    patient_id: int, 
    therapists_contacted: int,
    responses_received: int
) -> bool:
    """Send a status update email to a patient about their search progress.
    
    Args:
        patient_id: ID of the patient
        therapists_contacted: Number of therapists contacted
        responses_received: Number of responses received
        
    Returns:
        bool: True if email was sent successfully
    """
    subject = "Update zu Ihrer Therapieplatzsuche"
    
    body_html = f"""
    <p>Sehr geehrte/r Patient/in,</p>
    
    <p>wir möchten Sie über den aktuellen Stand Ihrer Therapieplatzsuche informieren:</p>
    
    <ul>
        <li><strong>Kontaktierte Therapeuten:</strong> {therapists_contacted}</li>
        <li><strong>Erhaltene Rückmeldungen:</strong> {responses_received}</li>
    </ul>
    
    <p>Wir setzen die Suche aktiv fort und informieren Sie, sobald sich neue 
    Möglichkeiten ergeben.</p>
    
    <p>Mit freundlichen Grüßen,<br>
    Ihr Therapieplatz-Vermittlungsteam</p>
    """
    
    body_text = f"""
    Sehr geehrte/r Patient/in,
    
    wir möchten Sie über den aktuellen Stand Ihrer Therapieplatzsuche informieren:
    
    - Kontaktierte Therapeuten: {therapists_contacted}
    - Erhaltene Rückmeldungen: {responses_received}
    
    Wir setzen die Suche aktiv fort und informieren Sie, sobald sich neue 
    Möglichkeiten ergeben.
    
    Mit freundlichen Grüßen,
    Ihr Therapieplatz-Vermittlungsteam
    """
    
    return send_patient_email(patient_id, subject, body_html, body_text)


def send_match_found_email(
    patient_id: int,
    therapist_name: str,
    therapist_address: str,
    therapist_phone: str,
    appointment_instructions: Optional[str] = None
) -> bool:
    """Send an email to notify patient that a therapist has accepted them.
    
    Args:
        patient_id: ID of the patient
        therapist_name: Name of the accepting therapist
        therapist_address: Address of the therapist
        therapist_phone: Phone number of the therapist
        appointment_instructions: Optional specific instructions
        
    Returns:
        bool: True if email was sent successfully
    """
    subject = "Gute Nachrichten - Therapieplatz gefunden!"
    
    instructions = appointment_instructions or "Bitte kontaktieren Sie die Praxis telefonisch, um einen ersten Termin zu vereinbaren."
    
    body_html = f"""
    <p>Sehr geehrte/r Patient/in,</p>
    
    <p><strong>Wir haben großartige Neuigkeiten für Sie!</strong></p>
    
    <p>{therapist_name} hat bestätigt, dass ein Therapieplatz für Sie zur Verfügung steht.</p>
    
    <p><strong>Kontaktdaten der Praxis:</strong></p>
    <ul>
        <li><strong>Name:</strong> {therapist_name}</li>
        <li><strong>Adresse:</strong> {therapist_address}</li>
        <li><strong>Telefon:</strong> {therapist_phone}</li>
    </ul>
    
    <p><strong>Nächste Schritte:</strong><br>
    {instructions}</p>
    
    <p>Wir wünschen Ihnen alles Gute für Ihre Therapie!</p>
    
    <p>Mit freundlichen Grüßen,<br>
    Ihr Therapieplatz-Vermittlungsteam</p>
    """
    
    body_text = f"""
    Sehr geehrte/r Patient/in,
    
    Wir haben großartige Neuigkeiten für Sie!
    
    {therapist_name} hat bestätigt, dass ein Therapieplatz für Sie zur Verfügung steht.
    
    Kontaktdaten der Praxis:
    - Name: {therapist_name}
    - Adresse: {therapist_address}
    - Telefon: {therapist_phone}
    
    Nächste Schritte:
    {instructions}
    
    Wir wünschen Ihnen alles Gute für Ihre Therapie!
    
    Mit freundlichen Grüßen,
    Ihr Therapieplatz-Vermittlungsteam
    """
    
    return send_patient_email(patient_id, subject, body_html, body_text)