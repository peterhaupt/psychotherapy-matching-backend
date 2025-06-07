"""Email sending utility functions."""
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from flask import current_app
from sqlalchemy import cast, String

from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from models.phone_call import PhoneCall
from utils.template_renderer import render_template
from utils.phone_call_scheduler import schedule_call_for_email
from shared.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Constants for email management
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
            PhoneCall.tatsaechliches_datum > threshold_date.date(),
            PhoneCall.status == 'completed'
        ).first()
        
        if recent_call:
            logger.info(f"Therapist {therapist_id} was called recently on {recent_call.tatsaechliches_datum}")
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
                to_email=email.empfaenger_email,
                subject=email.betreff,
                body_html=email.body_html,
                body_text=email.body_text,
                sender_email=email.absender_email,
                sender_name=email.absender_name
            )
            
            if success:
                email.status = EmailStatus.SENT
                email.sent_at = datetime.utcnow()
                sent_count += 1
                logger.info(f"Email {email.id} sent successfully")
            else:
                email.status = EmailStatus.FAILED
                email.fehlermeldung = "Failed to send email"
                email.wiederholungsanzahl += 1
                logger.error(f"Failed to send email {email.id}")
            
            db.commit()
            
            # Publish event if needed
            from events.producers import publish_email_sent
            if success:
                publish_email_sent(email.id, {
                    'therapist_id': email.therapist_id,
                    'betreff': email.betreff,
                    'status': email.status.value if hasattr(email.status, 'value') else str(email.status)
                })
        
        return sent_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending queued emails: {str(e)}")
        return sent_count
    finally:
        db.close()


def check_unanswered_emails():
    """Check for emails without responses after 7 days and schedule phone calls."""
    logger.info("Checking for unanswered emails older than 7 days")
    
    db = SessionLocal()
    try:
        # Find emails sent more than 7 days ago without a response
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        unanswered_emails = db.query(Email).filter(
            Email.sent_at <= seven_days_ago,
            cast(Email.status, String) == EmailStatus.SENT.value,
            Email.antwort_erhalten.is_(False)
        ).all()
        
        logger.info(f"Found {len(unanswered_emails)} unanswered emails older than 7 days")
        
        scheduled_count = 0
        for email in unanswered_emails:
            call_id = schedule_call_for_email(email.id)
            if call_id:
                scheduled_count += 1
                
        logger.info(f"Scheduled {scheduled_count} follow-up calls")
        return scheduled_count
        
    except Exception as e:
        logger.error(f"Error checking unanswered emails: {str(e)}")
        return 0
    finally:
        db.close()