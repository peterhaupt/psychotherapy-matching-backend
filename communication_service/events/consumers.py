"""Consumer for Kafka events in the Communication Service."""
import logging
import threading
from datetime import datetime, timedelta

from sqlalchemy import cast, String

from shared.kafka import EventSchema, KafkaConsumer
from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from utils.email_sender import send_queued_emails, check_unanswered_emails
from utils.phone_call_scheduler import schedule_call_for_email

# Initialize logging
logger = logging.getLogger(__name__)


def handle_matching_event(event: EventSchema) -> None:
    """Handle events from the matching service.

    Args:
        event: The event to process
    """
    logger.info(
        f"Processing matching event: {event.event_type}",
        extra={"event_id": event.event_id}
    )

    # The communication service now primarily listens for events
    # that indicate when to send emails or make calls
    # The bundle logic is now handled in the matching service
    
    if event.event_type == "communication.send_email":
        # Handle request to send an email
        email_id = event.payload.get("email_id")
        if email_id:
            db = SessionLocal()
            try:
                email = db.query(Email).filter(Email.id == email_id).first()
                if email and email.status == EmailStatus.In_Warteschlange:
                    # Send the email immediately
                    from utils.email_sender import send_email
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
                        logger.info(f"Sent email {email_id}")
                    else:
                        email.status = EmailStatus.Fehlgeschlagen
                        email.fehlermeldung = "Failed to send"
                        logger.error(f"Failed to send email {email_id}")
                    
                    db.commit()
            except Exception as e:
                logger.error(f"Error processing send_email event: {str(e)}")
            finally:
                db.close()
    
    elif event.event_type == "communication.schedule_call":
        # Handle request to schedule a phone call
        therapist_id = event.payload.get("therapist_id")
        email_id = event.payload.get("email_id")
        
        if therapist_id and email_id:
            call_id = schedule_call_for_email(email_id)
            if call_id:
                logger.info(f"Scheduled call {call_id} for email {email_id}")
            else:
                logger.warning(f"Failed to schedule call for email {email_id}")


def process_email_queue(event=None):
    """Process the email queue.
    
    Args:
        event: Optional event that triggered this processing
    """
    logger.info("Processing email queue")
    sent_count = send_queued_emails(limit=10)
    logger.info(f"Sent {sent_count} emails")


def check_unanswered_emails_worker():
    """Check for emails without responses after 7 days and schedule phone calls."""
    logger.info("Checking for unanswered emails older than 7 days")
    
    db = SessionLocal()
    try:
        # Find emails sent more than 7 days ago without a response
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        unanswered_emails = db.query(Email).filter(
            Email.gesendet_am <= seven_days_ago,
            cast(Email.status, String) == EmailStatus.Gesendet.value,
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


def start_consumers():
    """Start all Kafka consumers for the Communication Service."""
    try:
        # Consumer for matching events
        matching_consumer = KafkaConsumer(
            topics=["communication-events"],
            group_id="communication-service",
        )
        
        # Define the event types we're interested in
        communication_event_types = [
            "communication.send_email", 
            "communication.schedule_call"
        ]
        
        # Start processing in a separate thread
        matching_thread = threading.Thread(
            target=matching_consumer.process_events,
            args=(handle_matching_event, communication_event_types),
            daemon=True
        )
        matching_thread.start()
        
        # Start a thread to periodically process the email queue
        def email_queue_worker():
            import time
            while True:
                process_email_queue()
                time.sleep(60)  # Check every minute
        
        email_thread = threading.Thread(
            target=email_queue_worker,
            daemon=True
        )
        email_thread.start()
        
        # Start a thread to periodically check for unanswered emails
        def unanswered_email_checker():
            import time
            while True:
                check_unanswered_emails_worker()
                time.sleep(3600)  # Check once per hour
                
        unanswered_thread = threading.Thread(
            target=unanswered_email_checker,
            daemon=True
        )
        unanswered_thread.start()
        
        logger.info("Kafka consumers and processing workers initialized")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")