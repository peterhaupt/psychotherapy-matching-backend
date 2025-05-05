"""Consumer for Kafka events in the Communication Service."""
import logging
import threading

from shared.kafka import EventSchema, KafkaConsumer
from utils.email_sender import send_queued_emails

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
        # This could trigger an email to be created
        logger.info("New match created, consider sending notification email")
        
    elif event.event_type == "match.status_changed":
        # This could trigger different types of emails depending on new status
        new_status = event.payload.get("new_status")
        logger.info(f"Match status changed to {new_status}")


def process_email_queue(event=None):
    """Process the email queue.
    
    Args:
        event: Optional event that triggered this processing
    """
    logger.info("Processing email queue")
    sent_count = send_queued_emails(limit=10)
    logger.info(f"Sent {sent_count} emails")


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
        
        logger.info("Kafka consumers and email queue worker initialized")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")