"""Producer for therapist-related Kafka events."""
import logging
from typing import Dict, Any, Optional

from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = RobustKafkaProducer(service_name="therapist-service")

# Topic for therapist events
THERAPIST_TOPIC = "therapist-events"


def publish_therapist_created(
    therapist_id: int,
    therapist_data: Dict[str, Any]
) -> bool:
    """Publish an event when a new therapist is created.

    Args:
        therapist_id: ID of the created therapist
        therapist_data: Dict containing therapist data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=THERAPIST_TOPIC,
        event_type="therapist.created",
        payload={
            "therapist_id": therapist_id,
            "therapist_data": therapist_data
        },
        key=str(therapist_id)
    )


def publish_therapist_updated(
    therapist_id: int,
    therapist_data: Dict[str, Any]
) -> bool:
    """Publish an event when a therapist is updated.

    Args:
        therapist_id: ID of the updated therapist
        therapist_data: Dict containing updated therapist data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=THERAPIST_TOPIC,
        event_type="therapist.updated",
        payload={
            "therapist_id": therapist_id,
            "therapist_data": therapist_data
        },
        key=str(therapist_id)
    )


def publish_therapist_blocked(
    therapist_id: int,
    therapist_data: Dict[str, Any],
    reason: Optional[str] = None
) -> bool:
    """Publish an event when a therapist is blocked.

    Args:
        therapist_id: ID of the blocked therapist
        therapist_data: Dict containing therapist data
        reason: Optional reason for blocking

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=THERAPIST_TOPIC,
        event_type="therapist.blocked",
        payload={
            "therapist_id": therapist_id,
            "therapist_data": therapist_data,
            "reason": reason
        },
        key=str(therapist_id)
    )


def publish_therapist_unblocked(
    therapist_id: int,
    therapist_data: Dict[str, Any]
) -> bool:
    """Publish an event when a therapist is unblocked.

    Args:
        therapist_id: ID of the unblocked therapist
        therapist_data: Dict containing therapist data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=THERAPIST_TOPIC,
        event_type="therapist.unblocked",
        payload={
            "therapist_id": therapist_id,
            "therapist_data": therapist_data
        },
        key=str(therapist_id)
    )