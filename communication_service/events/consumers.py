"""Consumer for Kafka events in the Communication Service."""
import logging
import threading
from datetime import datetime, timedelta

from shared.kafka import EventSchema, KafkaConsumer
from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from models.email_batch import EmailBatch
from utils.email_sender import send_queued_emails, process_pending_requests
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

    # Handle different event types
    if event.event_type == "match.created":
        # This could trigger an email to be created via the batch processing
        logger.info("New match created, will be included in next batch processing")
        
        # Immediately process pending requests to include this new match
        processed_count = process_pending_requests()
        logger.info(f"Processed {processed_count} batches after new match")
        
    elif event.event_type == "match.status_changed":
        # This could trigger different types of emails depending on new status
        new_status = event.payload.get("new_status")
        match_id = event.payload.get("match_id")
        logger.info(f"Match {match_id} status changed to {new_status}")
        
        # Update any existing email batches that contain this match
        db = SessionLocal()
        try:
            # Find batches containing this placement request
            batches = db.query(EmailBatch).filter(
                EmailBatch.placement_request_id == match_id
            ).all()
            
            for batch in batches:
                # If match is no longer open, mark it as not included
                if new_status != "offen" and new_status != "in_bearbeitung":
                    batch.included = False
                    batch.response_notes = f"Status changed to {new_status}"
                    
            db.commit()
            logger.info(f"Updated {len(batches)} email batches for match {match_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating email batches: {str(e)}")
        finally:
            db.close()


def process_email_queue(event=None):
    """Process the email queue.
    
    Args:
        event: Optional event that triggered this processing
    """
    logger.info("Processing email queue")
    sent_count = send_queued_emails(limit=10)
    logger.info(f"Sent {sent_count} emails")


def check_unanswered_emails():
    """Check for emails without responses after 7 days and schedule phone calls."""
    logger.info("Checking for unanswered emails older than 7 days")
    
    db = SessionLocal()
    try:
        # Find emails sent more than 7 days ago without a response
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        unanswered_emails = db.query(Email).filter(
            Email.sent_at <= seven_days_ago,
            Email.status == EmailStatus.SENT,
            Email.response_received.is_(False)
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


def schedule_daily_batch_processing():
    """Run the daily batch processing for emails."""
    logger.info("Starting daily batch email processing")
    
    # Process pending requests to create new batch emails
    batch_count = process_pending_requests()
    logger.info(f"Created {batch_count} batch emails")
    
    # Process the email queue to send pending emails
    sent_count = send_queued_emails(limit=50)  # Higher limit for daily processing
    logger.info(f"Sent {sent_count} emails from queue")
    
    # Check for unanswered emails and schedule follow-up calls
    call_count = check_unanswered_emails()
    logger.info(f"Scheduled {call_count} follow-up calls for unanswered emails")


def start_consumers():
    """Start all Kafka consumers for the Communication Service."""
    try:
        # Consumer for matching events
        matching_consumer = KafkaConsumer(
            topics=["matching-events"],
            group_id="communication-service",
        )
        
        # Define the matching event types we're interested in
        matching_event_types = ["match.created", "match.status_changed"]
        
        # Start processing in a separate thread
        matching_thread = threading.Thread(
            target=matching_consumer.process_events,
            args=(handle_matching_event, matching_event_types),
            daemon=True
        )
        matching_thread.start()
        
        # Start a thread to periodically process the email queue
        # In a real implementation, this would be replaced with a proper scheduler
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
        def unanswered_email_worker():
            import time
            while True:
                check_unanswered_emails()
                time.sleep(3600)  # Check once per hour
                
        unanswered_thread = threading.Thread(
            target=unanswered_email_worker,
            daemon=True
        )
        unanswered_thread.start()
        
        # Start a thread for daily batch processing
        def daily_batch_worker():
            import time
            import datetime
            
            while True:
                # Get current time
                now = datetime.datetime.now()
                
                # Schedule the batch processing for 1 AM
                target_hour = 1
                
                # Calculate time until next run
                if now.hour >= target_hour:
                    # If it's already past target hour, wait until tomorrow
                    next_run = now.replace(day=now.day+1, hour=target_hour, 
                                          minute=0, second=0, microsecond=0)
                else:
                    # If it's before target hour, run today
                    next_run = now.replace(hour=target_hour, minute=0, 
                                          second=0, microsecond=0)
                
                # Calculate sleep time in seconds
                sleep_seconds = (next_run - now).total_seconds()
                
                logger.info(f"Next batch processing scheduled for {next_run}")
                
                # Sleep until next run time
                time.sleep(sleep_seconds)
                
                # Run the batch processing
                schedule_daily_batch_processing()
        
        batch_thread = threading.Thread(
            target=daily_batch_worker,
            daemon=True
        )
        batch_thread.start()
        
        logger.info("Kafka consumers and processing workers initialized")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")