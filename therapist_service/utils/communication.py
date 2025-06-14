"""Helper functions for therapist communication."""
import requests
import logging
from datetime import datetime
from typing import Optional

from shared.config import get_config
from models.therapist import Therapist
from shared.utils.database import SessionLocal

# Get configuration
config = get_config()
logger = logging.getLogger(__name__)


def send_therapist_email(
    therapist_id: int, 
    subject: str, 
    body_markdown: str,
    add_legal_footer: bool = True
) -> bool:
    """Send an email to a therapist via the communication service.
    
    Args:
        therapist_id: ID of the therapist to email
        subject: Email subject line
        body_markdown: Markdown content of the email (URLs will be auto-linked)
        add_legal_footer: Whether to add legal footer (default: True)
        
    Returns:
        bool: True if email was created successfully, False otherwise
    """
    db = SessionLocal()
    try:
        # Get therapist data
        therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
        if not therapist:
            logger.error(f"Therapist {therapist_id} not found")
            return False
            
        if not therapist.email:
            logger.warning(f"Therapist {therapist_id} has no email address")
            return False
        
        # Update last email contact date
        therapist.letzter_kontakt_email = datetime.utcnow().date()
        db.commit()
        
        # Send via communication service
        comm_url = config.get_service_url('communication', internal=True)
        
        # Create email request using markdown
        email_data = {
            'therapist_id': therapist_id,
            'betreff': subject,
            'inhalt_markdown': body_markdown,
            'empfaenger_email': therapist.email,
            'empfaenger_name': f"{therapist.titel or ''} {therapist.vorname} {therapist.nachname}".strip(),
            'add_legal_footer': add_legal_footer
        }
        
        response = requests.post(
            f"{comm_url}/api/emails",
            json=email_data
        )
        
        if response.ok:
            logger.info(f"Email created successfully for therapist {therapist_id}")
            return True
        else:
            logger.error(f"Failed to create email for therapist {therapist_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email to therapist {therapist_id}: {str(e)}")
        return False
    finally:
        db.close()


def schedule_therapist_call(
    therapist_id: int, 
    notes: str,
    scheduled_date: Optional[str] = None,
    scheduled_time: Optional[str] = None,
    duration_minutes: int = 5
) -> Optional[int]:
    """Schedule a phone call with a therapist.
    
    Args:
        therapist_id: ID of the therapist to call
        notes: Notes about the purpose of the call
        scheduled_date: Date for the call (YYYY-MM-DD format), uses auto-scheduling if not provided
        scheduled_time: Time for the call (HH:MM format), uses auto-scheduling if not provided
        duration_minutes: Duration of the call in minutes (default: 5)
        
    Returns:
        int: ID of the created phone call, or None if failed
    """
    db = SessionLocal()
    try:
        # Get therapist data
        therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
        if not therapist:
            logger.error(f"Therapist {therapist_id} not found")
            return None
            
        if not therapist.telefon:
            logger.warning(f"Therapist {therapist_id} has no phone number")
            return None
        
        # Update last phone contact date
        therapist.letzter_kontakt_telefon = datetime.utcnow().date()
        db.commit()
        
        # Send via communication service
        comm_url = config.get_service_url('communication', internal=True)
        
        # Create phone call request
        call_data = {
            'therapist_id': therapist_id,
            'notizen': notes,
            'dauer_minuten': duration_minutes
        }
        
        # Add date/time if provided (otherwise auto-scheduling will be used)
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
            logger.info(f"Phone call {call_id} scheduled for therapist {therapist_id}")
            return call_id
        else:
            logger.error(f"Failed to schedule call for therapist {therapist_id}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error scheduling call for therapist {therapist_id}: {str(e)}")
        return None
    finally:
        db.close()