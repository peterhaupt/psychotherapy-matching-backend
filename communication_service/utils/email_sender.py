"""Email sending utility functions - Business logic removed."""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from flask import current_app
from sqlalchemy import cast, String

from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from shared.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


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
            Email.status == EmailStatus.In_Warteschlange.value
        ).limit(limit).all()
        
        for email in queued_emails:
            # Update status to sending
            email.status = EmailStatus.Wird_gesendet
            db.commit()
            
            # Try to send
            success = send_email(
                to_email=email.empfaenger_email,
                subject=email.betreff,
                body_html=email.inhalt_html,
                body_text=email.inhalt_text,
                sender_email=email.absender_email,
                sender_name=email.absender_name
            )
            
            if success:
                email.status = EmailStatus.Gesendet
                email.gesendet_am = datetime.utcnow()
                sent_count += 1
                logger.info(f"Email {email.id} sent successfully")
            else:
                email.status = EmailStatus.Fehlgeschlagen
                email.fehlermeldung = "Failed to send email"
                email.wiederholungsanzahl += 1
                logger.error(f"Failed to send email {email.id}")
            
            db.commit()
        
        return sent_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending queued emails: {str(e)}")
        return sent_count
    finally:
        db.close()