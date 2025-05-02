"""Producer for matching-related Kafka events."""
import logging
from typing import Dict, Any, Optional

from shared.kafka import KafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = KafkaProducer(service_name="matching-service")

# Topic for matching events
MATCHING_TOPIC = "matching-events"


def publish_match_created(
    match_id: int,
    patient_id: int,
    therapist_id: int,
    match_data: Optional[Dict[str, Any]] = None
) -> bool:
    """Publish an event when a new match is created.

    Args:
        match_id: ID of the created match/placement request
        patient_id: ID of the patient
        therapist_id: ID of the therapist
        match_data: Optional additional match data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    payload = {
        "match_id": match_id,
        "patient_id": patient_id,
        "therapist_id": therapist_id
    }
    
    # Add additional data if provided
    if match_data:
        payload["match_data"] = match_data
    
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="match.created",
        payload=payload,
        key=str(match_id)
    )


def publish_match_status_changed(
    match_id: int,
    old_status: Optional[str],
    new_status: str,
    reason: Optional[str] = None
) -> bool:
    """Publish an event when a match status changes.

    Args:
        match_id: ID of the match with changed status
        old_status: Previous status value
        new_status: New status value
        reason: Optional reason for the status change

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    payload = {
        "match_id": match_id,
        "old_status": old_status,
        "new_status": new_status
    }
    
    # Add reason if provided
    if reason:
        payload["reason"] = reason
    
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="match.status_changed",
        payload=payload,
        key=str(match_id)
    )