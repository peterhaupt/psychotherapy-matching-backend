"""Email sending utility functions with PDF attachment support."""
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List

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


def _attach_pdf(msg: MIMEMultipart, file_path: str) -> bool:
    """Attach a PDF file to the email.
    
    Args:
        msg: The email message object
        file_path: Path to the PDF file
        
    Returns:
        bool: True if attachment was successful, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            return False
        
        # Check file size (limit to 10MB)
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            logger.error(f"PDF file too large: {file_path} ({file_size} bytes)")
            return False
        
        # Read the PDF file
        with open(file_path, 'rb') as f:
            pdf_data = f.read()
        
        # Create the attachment
        pdf_attachment = MIMEBase('application', 'pdf')
        pdf_attachment.set_payload(pdf_data)
        encoders.encode_base64(pdf_attachment)
        
        # Get filename from path
        filename = os.path.basename(file_path)
        
        # Add header with proper encoding for German characters
        pdf_attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{filename}"'
        )
        
        # Attach to message
        msg.attach(pdf_attachment)
        logger.info(f"Successfully attached PDF: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to attach PDF {file_path}: {str(e)}")
        return False


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    sender_email: Optional[str] = None,
    sender_name: Optional[str] = None,
    attachments: Optional[List[str]] = None
) -> bool:
    """Send an email using SMTP with optional PDF attachments.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body content (optional)
        sender_email: Sender email (optional, uses default if not provided)
        sender_name: Sender name (optional, uses default if not provided)
        attachments: List of file paths to attach (optional)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    smtp_settings = get_smtp_settings()
    
    # Use defaults if not provided
    sender_email = sender_email or smtp_settings['sender']
    sender_name = sender_name or smtp_settings['sender_name']
    
    # Create message - use 'mixed' to support attachments
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = to_email
    
    # Create the body part as 'alternative' for text/html
    msg_body = MIMEMultipart('alternative')
    
    # Add text and HTML parts to body
    if body_text:
        text_part = MIMEText(body_text, 'plain', 'utf-8')
        msg_body.attach(text_part)
    
    html_part = MIMEText(body_html, 'html', 'utf-8')
    msg_body.attach(html_part)
    
    # Attach the body to the main message
    msg.attach(msg_body)
    
    # Add PDF attachments if provided
    attachment_count = 0
    if attachments:
        logger.info(f"Processing {len(attachments)} attachments for email to {to_email}")
        for attachment_path in attachments:
            if attachment_path and isinstance(attachment_path, str):
                if _attach_pdf(msg, attachment_path):
                    attachment_count += 1
                else:
                    logger.warning(f"Failed to attach: {attachment_path}")
    
    if attachments and attachment_count > 0:
        logger.info(f"Successfully attached {attachment_count} PDF(s) to email")
    
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
        
        logger.info(f"Email sent successfully to {to_email} with {attachment_count} attachment(s)")
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
            
            # Parse attachments if stored as JSON
            attachments = None
            if hasattr(email, 'attachments') and email.attachments:
                if isinstance(email.attachments, list):
                    attachments = email.attachments
                elif isinstance(email.attachments, str):
                    # If stored as JSON string
                    import json
                    try:
                        attachments = json.loads(email.attachments)
                    except:
                        attachments = None
            
            # Try to send
            success = send_email(
                to_email=email.empfaenger_email,
                subject=email.betreff,
                body_html=email.inhalt_html,
                body_text=email.inhalt_text,
                sender_email=email.absender_email,
                sender_name=email.absender_name,
                attachments=attachments
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
