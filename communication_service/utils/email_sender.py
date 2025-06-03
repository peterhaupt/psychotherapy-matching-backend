"""Email sending utility functions."""
import logging
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any

from flask import current_app
from sqlalchemy import and_, or_, cast, String, func

from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from models.email_batch import EmailBatch
from models.phone_call import PhoneCall
from utils.template_renderer import render_template
from utils.phone_call_scheduler import schedule_call_for_email
from shared.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Constants for email batching
MAX_PATIENTS_PER_EMAIL = 5  # Maximum number of patients to include in a single email
MIN_DAYS_BETWEEN_EMAILS = 7  # Minimum days between emails to the same therapist


def get_smtp_settings():
    """Get SMTP settings from app config or use defaults.
    
    Returns:
        dict: SMTP settings
    """
    try:
        # Try to get settings from Flask app config
        return {
            'host': current_app.config.get('SMTP_HOST', config.SMTP_HOST),
            'port': current_app.config.get('SMTP_PORT', config.SMTP_PORT),
            'username': current_app.config.get('SMTP_USERNAME', config.SMTP_USERNAME),
            'password': current_app.config.get('SMTP_PASSWORD', config.SMTP_PASSWORD),
            'use_tls': current_app.config.get('SMTP_USE_TLS', config.SMTP_USE_TLS),
            'sender': current_app.config.get('EMAIL_SENDER', config.EMAIL_SENDER),
            'sender_name': current_app.config.get('EMAIL_SENDER_NAME', config.EMAIL_SENDER_NAME),
        }
    except RuntimeError:
        # Not running in Flask app context, use defaults from config
        return config.get_smtp_settings()


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    sender_email: Optional[str] = None,
    sender_name: Optional[str] = None
) -> bool:
    """Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body content (optional)
        sender_email: Sender email (optional, uses default if not provided)
        sender_name: Sender name (optional, uses default if not provided)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    smtp_settings = get_smtp_settings()
    
    # Use defaults if not provided
    sender_email = sender_email or smtp_settings['sender']
    sender_name = sender_name or smtp_settings['sender_name']
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = to_email
    
    # Add text and HTML parts
    if body_text:
        text_part = MIMEText(body_text, 'plain')
        msg.attach(text_part)
    
    html_part = MIMEText(body_html, 'html')
    msg.attach(html_part)
    
    try:
        # Connect to SMTP server
        if smtp_settings['use_tls']:
            server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
        
        # Login if credentials provided
        if smtp_settings['username'] and smtp_settings['password']:
            server.login(smtp_settings['username'], smtp_settings['password'])
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def can_contact_therapist(therapist_id: int, days_threshold: int = MIN_DAYS_BETWEEN_EMAILS) -> bool:
    """Check if a therapist can be contacted based on frequency rules.
    
    Args:
        therapist_id: ID of the therapist
        days_threshold: Minimum days between contacts
        
    Returns:
        bool: True if therapist can be contacted
    """
    db = SessionLocal()
    try:
        # Check last email sent to this therapist
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        recent_email = db.query(Email).filter(
            Email.therapist_id == therapist_id,
            Email.sent_at > threshold_date,
            Email.status == EmailStatus.SENT.value
        ).first()
        
        if recent_email:
            logger.info(f"Therapist {therapist_id} was contacted recently on {recent_email.sent_at}")
            return False
            
        # Also check phone calls
        recent_call = db.query(PhoneCall).filter(
            PhoneCall.therapist_id == therapist_id,
            PhoneCall.actual_date > threshold_date.date(),
            PhoneCall.status == 'completed'
        ).first()
        
        if recent_call:
            logger.info(f"Therapist {therapist_id} was called recently on {recent_call.actual_date}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking therapist contact history: {str(e)}")
        return False
    finally:
        db.close()


def send_queued_emails(limit: int = 10) -> int:
    """Send emails that are queued for sending.
    
    Args:
        limit: Maximum number of emails to send in one batch
        
    Returns:
        int: Number of emails sent
    """
    db = SessionLocal()
    sent_count = 0
    
    try:
        # Get queued emails
        queued_emails = db.query(Email).filter(
            Email.status == EmailStatus.QUEUED.value
        ).limit(limit).all()
        
        for email in queued_emails:
            # Update status to sending
            email.status = EmailStatus.SENDING
            db.commit()
            
            # Try to send
            success = send_email(
                to_email=email.recipient_email,
                subject=email.subject,
                body_html=email.body_html,
                body_text=email.body_text,
                sender_email=email.sender_email,
                sender_name=email.sender_name
            )
            
            if success:
                email.status = EmailStatus.SENT
                email.sent_at = datetime.utcnow()
                sent_count += 1
                logger.info(f"Email {email.id} sent successfully")
            else:
                email.status = EmailStatus.FAILED
                email.error_message = "Failed to send email"
                email.retry_count += 1
                logger.error(f"Failed to send email {email.id}")
            
            db.commit()
            
            # Publish event if needed
            from events.producers import publish_email_sent
            if success:
                publish_email_sent(email.id, {
                    'therapist_id': email.therapist_id,
                    'subject': email.subject,
                    'status': email.status.value if hasattr(email.status, 'value') else str(email.status)
                })
        
        return sent_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending queued emails: {str(e)}")
        return sent_count
    finally:
        db.close()


def create_batch_email(
    therapist_id: int,
    placement_requests: List[Dict[str, Any]],
    template_name: str = "batch_request.html"
) -> Optional[int]:
    """Create a batch email for multiple placement requests.
    
    Args:
        therapist_id: ID of the therapist
        placement_requests: List of placement request data
        template_name: Name of the email template to use
        
    Returns:
        int: ID of created email or None if failed
    """
    import requests
    
    db = SessionLocal()
    try:
        # Get therapist data
        from shared.config import get_config
        config = get_config()
        therapist_url = f"{config.get_service_url('therapist', internal=True)}/api/therapists/{therapist_id}"
        response = requests.get(therapist_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to get therapist {therapist_id}")
            return None
            
        therapist = response.json()
        
        # Get patient data for each placement request
        patients = []
        patient_service_url = config.get_service_url('patient', internal=True)
        
        for pr in placement_requests[:MAX_PATIENTS_PER_EMAIL]:
            patient_response = requests.get(f"{patient_service_url}/api/patients/{pr['patient_id']}")
            if patient_response.status_code == 200:
                patients.append(patient_response.json())
        
        if not patients:
            logger.error("No patient data found for batch email")
            return None
        
        # Render email content
        context = {
            'recipient_name': f"{therapist.get('titel', '')} {therapist['nachname']}".strip(),
            'patients': patients,
            'sender_email': config.EMAIL_SENDER,
            'sender_name': config.EMAIL_SENDER_NAME,
            'current_year': datetime.now().year
        }
        
        body_html = render_template(f"emails/{template_name}", **context)
        
        # Create plain text version
        body_text = f"""
Sehr geehrte(r) {context['recipient_name']},

wir haben mehrere Patienten, für die wir einen Therapieplatz suchen.
Bitte antworten Sie auf diese E-Mail, wenn Sie Kapazitäten haben.

Mit freundlichen Grüßen,
{context['sender_name']}
        """
        
        # Create email record
        batch_id = str(uuid.uuid4())
        
        email = Email(
            therapist_id=therapist_id,
            subject=f"Therapieplatz-Anfrage für {len(patients)} Patient(en)",
            body_html=body_html,
            body_text=body_text,
            recipient_email=therapist['email'],
            recipient_name=context['recipient_name'],
            sender_email=config.EMAIL_SENDER,
            sender_name=config.EMAIL_SENDER_NAME,
            status=EmailStatus.QUEUED,
            batch_id=batch_id,
            queued_at=datetime.utcnow()
        )
        
        db.add(email)
        db.flush()
        
        # Create email batches
        for i, pr in enumerate(placement_requests[:MAX_PATIENTS_PER_EMAIL]):
            batch = EmailBatch(
                email_id=email.id,
                placement_request_id=pr['id'],
                priority=i + 1,
                included=True
            )
            db.add(batch)
        
        db.commit()
        
        logger.info(f"Created batch email {email.id} for therapist {therapist_id} with {len(patients)} patients")
        return email.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating batch email: {str(e)}")
        return None
    finally:
        db.close()


def process_pending_requests() -> int:
    """Process pending placement requests and create batch emails.
    
    Returns:
        int: Number of batch emails created
    """
    import requests
    from collections import defaultdict
    
    db = SessionLocal()
    batch_count = 0
    
    try:
        # Get pending placement requests from matching service
        config = get_config()
        matching_url = f"{config.get_service_url('matching', internal=True)}/api/placement-requests"
        response = requests.get(matching_url, params={'status': 'offen'})
        
        if response.status_code != 200:
            logger.error("Failed to get placement requests")
            return 0
        
        placement_requests = response.json()
        
        # Group by therapist
        requests_by_therapist = defaultdict(list)
        for pr in placement_requests:
            therapist_id = pr['therapist_id']
            
            # Check if we can contact this therapist
            if can_contact_therapist(therapist_id):
                requests_by_therapist[therapist_id].append(pr)
        
        # Create batch emails
        for therapist_id, requests in requests_by_therapist.items():
            # Sort by creation date (oldest first)
            requests.sort(key=lambda x: x.get('created_at', ''))
            
            # Create email
            email_id = create_batch_email(therapist_id, requests)
            if email_id:
                batch_count += 1
                
                # Update placement request status
                for pr in requests[:MAX_PATIENTS_PER_EMAIL]:
                    update_url = f"{matching_url}/{pr['id']}"
                    requests.put(update_url, json={'status': 'in_bearbeitung'})
        
        logger.info(f"Created {batch_count} batch emails")
        return batch_count
        
    except Exception as e:
        logger.error(f"Error processing pending requests: {str(e)}")
        return batch_count
    finally:
        db.close()