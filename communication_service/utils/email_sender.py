"""Email sending utility functions."""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus

# Configure logging
logger = logging.getLogger(__name__)

# SMTP Settings
SMTP_HOST = "127.0.0.1"
SMTP_PORT = 1025
SMTP_USERNAME = "therapieplatz@peterhaupt.de"
SMTP_PASSWORD = "***REMOVED_EXPOSED_PASSWORD***"
SMTP_USE_TLS = True
DEFAULT_SENDER = "therapieplatz@peterhaupt.de"
DEFAULT_SENDER_NAME = "Boona Therapieplatz-Vermittlung"


def send_email(email_id):
    """Send an email from the database.
    
    Args:
        email_id: ID of the email to send
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    db = SessionLocal()
    try:
        # Get the email from the database
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email with ID {email_id} not found")
            return False
        
        # Update status to SENDING
        email.status = EmailStatus.SENDING
        db.commit()
        
        # Create the email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email.subject
        msg['From'] = f"{email.sender_name} <{email.sender_email}>"
        msg['To'] = f"{email.recipient_name} <{email.recipient_email}>"
        
        # Attach the plain text and HTML versions
        text_part = MIMEText(email.body_text, 'plain')
        html_part = MIMEText(email.body_html, 'html')
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send the email
        try:
            # Connect to the SMTP server
            if SMTP_USE_TLS:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            
            # Login if credentials are provided
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            # Send the email
            server.sendmail(
                email.sender_email,
                email.recipient_email,
                msg.as_string()
            )
            
            # Close the connection
            server.quit()
            
            # Update the email status
            email.status = EmailStatus.SENT
            email.sent_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Email {email_id} sent successfully")
            return True
            
        except Exception as e:
            # Update the email status
            email.status = EmailStatus.FAILED
            email.error_message = str(e)
            email.retry_count += 1
            db.commit()
            
            logger.error(f"Failed to send email {email_id}: {str(e)}")
            return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing email {email_id}: {str(e)}")
        return False
    finally:
        db.close()


def send_queued_emails(limit=10):
    """Send queued emails.
    
    Args:
        limit: Maximum number of emails to send
        
    Returns:
        int: Number of emails sent successfully
    """
    db = SessionLocal()
    try:
        # Get queued emails
        emails = db.query(Email).filter(
            Email.status == EmailStatus.QUEUED
        ).order_by(Email.queued_at).limit(limit).all()
        
        sent_count = 0
        for email in emails:
            if send_email(email.id):
                sent_count += 1
        
        return sent_count
    except Exception as e:
        logger.error(f"Error sending queued emails: {str(e)}")
        return 0
    finally:
        db.close()