"""Consumer for Kafka events in the Matching Service."""
import logging

from shared.kafka import EventSchema

# Initialize logging
logger = logging.getLogger(__name__)


def handle_patient_event(event: EventSchema) -> None:
    """Handle events from the patient service.

    Args:
        event: The event to process
    """
    logger.info(
        f"Processing patient event: {event.event_type}",
        extra={"event_id": event.event_id}
    )

    # Handle different event types
    if event.event_type == "patient.deleted":
        # TODO: Implement bundle system logic for patient deletion
        patient_id = event.payload.get("patient_id")
        logger.info(f"Patient {patient_id} deleted - bundle system implementation pending")


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
        # TODO: Implement bundle system logic for therapist blocking
        therapist_id = event.payload.get("therapist_id")
        reason = event.payload.get("reason", "Therapist blocked")
        logger.info(f"Therapist {therapist_id} blocked: {reason} - bundle system implementation pending")


def start_consumers():
    """Start all Kafka consumers for the Matching Service."""
    try:
        # TODO: Re-enable consumers when bundle system is implemented
        logger.info("Kafka consumers temporarily disabled - bundle system implementation pending")
        
        # Will be re-enabled with bundle system:
        # - Patient event consumer
        # - Therapist event consumer
        # - Communication event consumer (for response handling)
        
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")