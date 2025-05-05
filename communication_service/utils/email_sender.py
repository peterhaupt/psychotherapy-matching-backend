"""Email sending utility functions."""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app
from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from utils.template_renderer import render_template

# Configure logging
logger = logging.getLogger(__name__)

# Default SMTP settings (will be overridden by app config if available)
DEFAULT_SMTP_HOST = "127.0.0.1"
DEFAULT_SMTP_PORT = 1025
DEFAULT_SMTP_USERNAME = "therapieplatz@peterhaupt.de"
DEFAULT_SMTP_PASSWORD = "***REMOVED_EXPOSED_PASSWORD***"
DEFAULT_SMTP_USE_TLS = True
DEFAULT_SENDER = "therapieplatz@peterhaupt.de"
DEFAULT_SENDER_NAME = "Boona Therapieplatz-Vermittlung"


def get_smtp_settings():
    """Get SMTP settings from app config or use defaults.
    
    Returns:
        dict: SMTP settings
    """
    try:
        # Try to get settings from Flask app config
        return {
            'host': current_app.config.get('SMTP_HOST', DEFAULT_SMTP_HOST),
            'port': current_app.config.get('SMTP_PORT', DEFAULT_SMTP_PORT),
            'username': current_app.config.get('SMTP_USERNAME', DEFAULT_SMTP_USERNAME),
            'password': current_app.config.get('SMTP_PASSWORD', DEFAULT_SMTP_PASSWORD),
            'use_tls': current_app.config.get('SMTP_USE_TLS', DEFAULT_SMTP_USE_TLS),
            'sender': current_app.config.get('EMAIL_SENDER', DEFAULT_SENDER),
            'sender_name': current_app.config.get('EMAIL_SENDER_NAME', DEFAULT_SENDER_NAME),
        }
    except RuntimeError:
        # Not running in Flask app context, use defaults
        return {
            'host': DEFAULT_SMTP_HOST,
            'port': DEFAULT_SMTP_PORT,
            'username': DEFAULT_SMTP_USERNAME,
            'password': DEFAULT_SMTP_PASSWORD,
            'use_tls': DEFAULT_SMTP_USE_TLS,
            'sender': DEFAULT_SENDER,
            'sender_name': DEFAULT_SENDER_NAME,
        }


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
        
        # Attach the plain text version
        text_part = MIMEText(email.body_text, 'plain')
        msg.attach(text_part)
        
        # Get SMTP settings
        smtp_settings = get_smtp_settings()
        
        # Send the email
        try:
            # Connect to the SMTP server
            if smtp_settings['use_tls']:
                server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
            
            # Login if credentials are provided
            if smtp_settings['username'] and smtp_settings['password']:
                server.login(smtp_settings['username'], smtp_settings['password'])
            
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
    """Send queued emails."""
    db = SessionLocal()
    try:
        logger.info("Starting send_queued_emails with systematic approach")
        
        # Method 1: Use a hybrid approach with direct value casting
        from sqlalchemy import cast, String, literal_column
        
        # Create a query that casts the status column to string and compares with the enum value
        query = db.query(Email).filter(
            cast(Email.status, String) == EmailStatus.QUEUED.value
        )
        
        # Log the actual SQL being generated
        sql_str = str(query.statement.compile(
            compile_kwargs={"literal_binds": True}
        ))
        logger.info(f"Generated SQL: {sql_str}")
        
        # Execute the query
        emails = query.order_by(Email.queued_at).limit(limit).all()
        
        logger.info(f"Found {len(emails)} emails with QUEUED status")
        
        sent_count = 0
        for email in emails:
            logger.info(f"Processing email {email.id} with status {email.status}")
            if send_email(email.id):
                sent_count += 1
        
        logger.info(f"Successfully sent {sent_count} emails")
        return sent_count
    except Exception as e:
        logger.error(f"Error sending queued emails: {str(e)}", exc_info=True)
        return 0
    finally:
        db.close()