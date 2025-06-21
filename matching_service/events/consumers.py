"""Consumer for Kafka events in the Matching Service."""
import logging
import threading
from datetime import datetime, timedelta

from shared.kafka import EventSchema, KafkaConsumer
from db import get_db_context
from models import Platzsuche, Therapeutenanfrage
from models.platzsuche import SuchStatus

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

    # Handle patient deletion
    if event.event_type == "patient.deleted":
        patient_id = event.payload.get("patient_id")
        if not patient_id:
            logger.error("Patient deletion event missing patient_id")
            return
            
        logger.info(f"Handling deletion of patient {patient_id}")
        
        try:
            with get_db_context() as db:
                # Cancel all active searches for this patient
                active_searches = db.query(Platzsuche).filter(
                    Platzsuche.patient_id == patient_id,
                    Platzsuche.status == SuchStatus.aktiv
                ).all()
                
                for search in active_searches:
                    search.cancel_search("Patient deleted from system")
                    logger.info(f"Cancelled search {search.id} for deleted patient {patient_id}")
                
                # Note: We don't remove patients from existing Therapeutenanfrage
                # because we want to maintain history. The anfrage stays as-is.
                
                db.commit()
                logger.info(f"Successfully handled deletion of patient {patient_id}")
                
        except Exception as e:
            logger.error(f"Error handling patient deletion: {str(e)}", exc_info=True)
    
    elif event.event_type == "patient.updated":
        # Log for future implementation
        patient_id = event.payload.get("patient_id")
        logger.info(f"Patient {patient_id} updated - no action taken (future enhancement)")
    
    else:
        logger.debug(f"Ignoring patient event type: {event.event_type}")


def handle_therapist_event(event: EventSchema) -> None:
    """Handle events from the therapist service.

    Args:
        event: The event to process
    """
    logger.info(
        f"Processing therapist event: {event.event_type}",
        extra={"event_id": event.event_id}
    )

    # Handle therapist blocking
    if event.event_type == "therapist.blocked":
        therapist_id = event.payload.get("therapist_id")
        reason = event.payload.get("reason", "Therapist blocked")
        
        if not therapist_id:
            logger.error("Therapist blocked event missing therapist_id")
            return
            
        logger.info(f"Handling blocking of therapist {therapist_id}: {reason}")
        
        try:
            with get_db_context() as db:
                # Cancel all unsent anfragen for this therapist
                unsent_anfragen = db.query(Therapeutenanfrage).filter(
                    Therapeutenanfrage.therapist_id == therapist_id,
                    Therapeutenanfrage.gesendet_datum.is_(None)
                ).all()
                
                for anfrage in unsent_anfragen:
                    # Add note about cancellation
                    anfrage.add_note(f"Cancelled: Therapist blocked - {reason}", author="System")
                    
                    # Note: We don't delete the anfrage, just mark it with a note
                    # This preserves the audit trail
                    logger.info(f"Marked anfrage {anfrage.id} as cancelled due to therapist block")
                
                # Add therapist to exclusion lists of patients in active searches
                # who have pending anfragen with this therapist
                sent_anfragen = db.query(Therapeutenanfrage).filter(
                    Therapeutenanfrage.therapist_id == therapist_id,
                    Therapeutenanfrage.gesendet_datum.isnot(None),
                    Therapeutenanfrage.antwort_datum.is_(None)
                ).all()
                
                for anfrage in sent_anfragen:
                    for ap in anfrage.anfrage_patients:
                        if ap.platzsuche and ap.platzsuche.status == SuchStatus.aktiv:
                            ap.platzsuche.exclude_therapist(
                                therapist_id, 
                                reason=f"Therapist blocked: {reason}"
                            )
                            logger.info(
                                f"Added therapist {therapist_id} to exclusion list "
                                f"for patient search {ap.platzsuche_id}"
                            )
                
                db.commit()
                logger.info(f"Successfully handled blocking of therapist {therapist_id}")
                
        except Exception as e:
            logger.error(f"Error handling therapist blocking: {str(e)}", exc_info=True)
    
    elif event.event_type == "therapist.unblocked":
        therapist_id = event.payload.get("therapist_id")
        logger.info(f"Therapist {therapist_id} unblocked - no automatic action taken")
        # Note: We don't automatically remove from exclusion lists
        # This requires manual review
    
    else:
        logger.debug(f"Ignoring therapist event type: {event.event_type}")


def handle_communication_event(event: EventSchema) -> None:
    """Handle events from the communication service.

    Args:
        event: The event to process
    """
    logger.info(
        f"Processing communication event: {event.event_type}",
        extra={"event_id": event.event_id}
    )
    
    # For now, just log these events
    # Future implementation would handle email responses
    if event.event_type == "communication.email_sent":
        logger.debug("Email sent event - no action needed")
    elif event.event_type == "communication.email_response_received":
        logger.info("Email response received - manual processing required (future enhancement)")
    else:
        logger.debug(f"Ignoring communication event type: {event.event_type}")


def start_consumers():
    """Start all Kafka consumers for the Matching Service."""
    try:
        logger.info("Starting Kafka consumers for Matching Service")
        
        # Consumer for patient events
        patient_consumer = KafkaConsumer(
            topics=["patient-events"],
            group_id="matching-service-patient",
        )
        
        # Consumer for therapist events  
        therapist_consumer = KafkaConsumer(
            topics=["therapist-events"],
            group_id="matching-service-therapist",
        )
        
        # Consumer for communication events
        communication_consumer = KafkaConsumer(
            topics=["communication-events"],
            group_id="matching-service-communication",
        )
        
        # Define the event types we're interested in
        patient_event_types = ["patient.created", "patient.updated", "patient.deleted"]
        therapist_event_types = ["therapist.blocked", "therapist.unblocked", "therapist.updated"]
        communication_event_types = ["communication.email_sent", "communication.email_response_received"]
        
        # Start processing in separate threads
        patient_thread = threading.Thread(
            target=patient_consumer.process_events,
            args=(handle_patient_event, patient_event_types),
            daemon=True,
            name="patient-event-consumer"
        )
        patient_thread.start()
        
        therapist_thread = threading.Thread(
            target=therapist_consumer.process_events,
            args=(handle_therapist_event, therapist_event_types),
            daemon=True,
            name="therapist-event-consumer"
        )
        therapist_thread.start()
        
        communication_thread = threading.Thread(
            target=communication_consumer.process_events,
            args=(handle_communication_event, communication_event_types),
            daemon=True,
            name="communication-event-consumer"
        )
        communication_thread.start()
        
        logger.info("Kafka consumers started successfully")
        logger.info("Listening for patient deletion and therapist blocking events")
        logger.info("Other events are logged for future implementation")
        
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}", exc_info=True)
        # Don't crash the service if Kafka is unavailable
        logger.warning("Service will continue without event consumers")
