"""Email queue processing for automated sending of queued emails."""
import os
import time
import logging
from datetime import datetime
from typing import Optional

from shared.config import get_config
from .email_sender import send_queued_emails
from .email_status import EmailQueueStatus

logger = logging.getLogger(__name__)


class EmailQueueProcessor:
    """Process queued emails in background.
    
    Continuously monitors for emails with status 'In_Warteschlange' 
    and sends them using SMTP.
    """
    
    def __init__(self):
        """Initialize the email queue processor."""
        self.config = get_config()
        
        # Get configuration from environment variables
        check_interval_str = os.environ.get('EMAIL_QUEUE_CHECK_INTERVAL_SECONDS', '30')
        batch_size_str = os.environ.get('EMAIL_QUEUE_BATCH_SIZE', '10')
        
        try:
            self.check_interval = int(check_interval_str)
            self.batch_size = int(batch_size_str)
        except ValueError:
            # Fallback to defaults
            self.check_interval = 30
            self.batch_size = 10
            logger.warning(f"Invalid config values, using defaults: interval={self.check_interval}, batch={self.batch_size}")
        
        logger.info(f"Email Queue Processor initialized")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Batch size: {self.batch_size} emails per run")
    
    def run(self):
        """Main processing loop."""
        logger.info("Starting email queue processing...")
        
        while True:
            try:
                # Update status
                EmailQueueStatus.update_last_check()
                
                # Process queued emails
                sent_count = send_queued_emails(limit=self.batch_size)
                
                if sent_count > 0:
                    logger.info(f"Sent {sent_count} emails in this batch")
                    EmailQueueStatus.record_emails_sent(sent_count)
                else:
                    logger.debug("No emails to send in this batch")
                
            except Exception as e:
                logger.error(f"Error in email queue processing loop: {str(e)}", exc_info=True)
                EmailQueueStatus.record_error(str(e))
                
                # Send notification about queue error (avoid infinite loop by not queuing)
                try:
                    self._send_error_notification(
                        "Email Queue Processor Error",
                        f"The email queue processor encountered an error:\n\n{str(e)}"
                    )
                except:
                    # If notification fails, just log it
                    logger.error("Failed to send error notification")
            
            # Wait before next check
            time.sleep(self.check_interval)
    
    def _send_error_notification(self, subject: str, body: str):
        """Send error notification directly (not through queue).
        
        Args:
            subject: Email subject
            body: Email body
        """
        try:
            # Import here to avoid circular dependency
            from .email_sender import send_email
            
            # Send directly to system notification email
            send_email(
                to_email=self.config.SYSTEM_NOTIFICATION_EMAIL,
                subject=f"[Communication Service] {subject}",
                body_html=f"<pre>{body}</pre>",
                body_text=body,
                sender_email=self.config.EMAIL_SENDER,
                sender_name="Email Queue System"
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")


def start_email_queue_processor():
    """Start the email queue processing in a background thread."""
    try:
        processor = EmailQueueProcessor()
        processor.run()
    except Exception as e:
        logger.error(f"Failed to start email queue processor: {str(e)}", exc_info=True)
        EmailQueueStatus.record_error(f"Processor startup failed: {str(e)}")