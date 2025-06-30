"""Consumer for Kafka events in the Patient Service."""
import logging
import threading
from datetime import date

from shared.kafka import EventSchema, KafkaConsumer
from models.patient import Patient
from shared.utils.database import SessionLocal

# Initialize logging
logger = logging.getLogger(__name__)


def handle_therapist_event(event: EventSchema) -> None:
    """Handle events from the therapist service.

    Args:
        event: The event to process
    """
    logger.info(
        f"Processing therapist event: {event.event_type}",
        extra={"event_id": event.event_id}
    )

    # Handle different event types
    if event.event_type == "therapist.blocked":
        # For example, update patient records where this therapist is assigned
        therapist_id = event.payload.get("therapist_id")
        logger.info(f"Therapist {therapist_id} has been blocked")
        # Implement specific handling logic here


def handle_communication_event(event: EventSchema) -> None:
    """Handle communication events to update letzter_kontakt.
    
    PHASE 2: New handler for automatic letzter_kontakt updates.
    
    Args:
        event: The event to process
    """
    logger.info(
        f"Processing communication event: {event.event_type}",
        extra={"event_id": event.event_id}
    )
    
    # Only process events that indicate successful communication
    if event.event_type not in ["email.sent", "email.response_received", "phone_call.completed"]:
        logger.debug(f"Ignoring event type: {event.event_type}")
        return
    
    # Extract patient_id from the event payload
    patient_id = event.payload.get("patient_id")
    if not patient_id:
        logger.debug("No patient_id in event payload, skipping")
        return  # Skip if no patient involved
    
    # Update patient's letzter_kontakt
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            # Update to today's date
            old_date = patient.letzter_kontakt
            patient.letzter_kontakt = date.today()
            db.commit()
            
            logger.info(
                f"Updated letzter_kontakt for patient {patient_id} "
                f"from {old_date} to {date.today()} "
                f"based on {event.event_type}"
            )
        else:
            logger.warning(f"Patient {patient_id} not found in database")
    except Exception as e:
        logger.error(f"Error updating letzter_kontakt for patient {patient_id}: {str(e)}")
        db.rollback()
    finally:
        db.close()


def start_consumers():
    """Start all Kafka consumers for the Patient Service."""
    try:
        # PHASE 2: Consumer for communication events
        comm_consumer = KafkaConsumer(
            topics=["communication-events"],
            group_id="patient-service-comm",
        )
        
        # Define the event types we're interested in for letzter_kontakt updates
        comm_event_types = ["email.sent", "email.response_received", "phone_call.completed"]
        
        # Start processing communication events in a separate thread
        comm_thread = threading.Thread(
            target=comm_consumer.process_events,
            args=(handle_communication_event, comm_event_types),
            daemon=True
        )
        comm_thread.start()
        
        logger.info("Communication event consumer started successfully")
        
        # Future: Therapist event consumer (currently commented out)
        # When therapist service is implemented, uncomment this:
        """
        therapist_consumer = KafkaConsumer(
            topics=["therapist-events"],
            group_id="patient-service",
        )
        
        therapist_event_types = ["therapist.blocked", "therapist.unblocked"]
        
        therapist_thread = threading.Thread(
            target=therapist_consumer.process_events,
            args=(handle_therapist_event, therapist_event_types),
            daemon=True
        )
        therapist_thread.start()
        """
        
        logger.info("All Kafka consumers initialized")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}", exc_info=True)