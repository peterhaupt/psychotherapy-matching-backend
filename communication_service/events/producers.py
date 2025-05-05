"""Producer for communication-related Kafka events."""
import logging
from typing import Dict, Any

from shared.kafka import KafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = KafkaProducer(service_name="communication-service")

# Topic for communication events
COMMUNICATION_TOPIC = "communication-events"


def publish_email_created(email_id: int, email_data: Dict[str, Any]) -> bool:
    """Publish an event when a new email is created.

    Args:
        email_id: ID of the created email
        email_data: Dict containing email data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="communication.email_created",
        payload={
            "email_id": email_id,
            "email_data": email_data
        },
        key=str(email_id)
    )


def publish_email_sent(email_id: int, email_data: Dict[str, Any]) -> bool:
    """Publish an event when an email is sent.

    Args:
        email_id: ID of the sent email
        email_data: Dict containing email data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="communication.email_sent",
        payload={
            "email_id": email_id,
            "email_data": email_data
        },
        key=str(email_id)
    )