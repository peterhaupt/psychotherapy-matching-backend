"""Consumer for Kafka events in the Matching Service."""
import logging

from shared.kafka import EventSchema, KafkaConsumer
from shared.utils.database import SessionLocal
from models.placement_request import PlacementRequest, PlacementRequestStatus

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
        # If a patient is deleted, cancel their placement requests
        patient_id = event.payload.get("patient_id")
        if patient_id:
            db = SessionLocal()
            try:
                # Find all open placement requests for this patient
                requests = db.query(PlacementRequest).filter(
                    PlacementRequest.patient_id == patient_id,
                    PlacementRequest.status.in_([
                        PlacementRequestStatus.OPEN,
                        PlacementRequestStatus.IN_PROGRESS
                    ])
                ).all()
                
                # Update status to canceled (we'll use REJECTED as the closest equivalent)
                for request in requests:
                    request.status = PlacementRequestStatus.REJECTED
                    request.notes = f"{request.notes or ''}\nPatient deleted from system."
                
                db.commit()
                logger.info(f"Canceled {len(requests)} placement requests for deleted patient {patient_id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error handling patient.deleted event: {str(e)}")
            finally:
                db.close()


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
        # If a therapist is blocked, suspend their placement requests
        therapist_id = event.payload.get("therapist_id")
        reason = event.payload.get("reason", "Therapist blocked")
        
        if therapist_id:
            db = SessionLocal()
            try:
                # Find all open placement requests for this therapist
                requests = db.query(PlacementRequest).filter(
                    PlacementRequest.therapist_id == therapist_id,
                    PlacementRequest.status.in_([
                        PlacementRequestStatus.OPEN, 
                        PlacementRequestStatus.IN_PROGRESS
                    ])
                ).all()
                
                # Update status to rejected
                for request in requests:
                    request.status = PlacementRequestStatus.REJECTED
                    request.notes = f"{request.notes or ''}\nTherapist blocked: {reason}"
                
                db.commit()
                logger.info(f"Suspended {len(requests)} placement requests for blocked therapist {therapist_id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error handling therapist.blocked event: {str(e)}")
            finally:
                db.close()


def start_consumers():
    """Start all Kafka consumers for the Matching Service."""
    try:
        # Consumer for patient events
        patient_consumer = KafkaConsumer(
            topics=["patient-events"],
            group_id="matching-service",
        )
        
        # Define the patient event types we're interested in
        patient_event_types = ["patient.created", "patient.updated", "patient.deleted"]
        
        # Consumer for therapist events
        therapist_consumer = KafkaConsumer(
            topics=["therapist-events"],
            group_id="matching-service",
        )
        
        # Define the therapist event types we're interested in
        therapist_event_types = [
            "therapist.created", 
            "therapist.updated",
            "therapist.blocked",
            "therapist.unblocked"
        ]
        
        # Start processing in separate threads
        import threading
        
        # Start patient event consumer thread
        patient_thread = threading.Thread(
            target=patient_consumer.process_events,
            args=(handle_patient_event, patient_event_types),
            daemon=True
        )
        patient_thread.start()
        
        # Start therapist event consumer thread
        therapist_thread = threading.Thread(
            target=therapist_consumer.process_events,
            args=(handle_therapist_event, therapist_event_types),
            daemon=True
        )
        therapist_thread.start()
        
        logger.info("Kafka consumers initialized")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")