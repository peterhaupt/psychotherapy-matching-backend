"""Producer for communication-related Kafka events."""
import logging
from typing import Dict, List, Optional, Any

# Import our robust producer instead of the shared one
from events.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer with robust implementation
producer = RobustKafkaProducer(service_name="communication-service")

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


def publish_phone_call_scheduled(call_id: int, call_data: Dict[str, Any]) -> bool:
    """Publish an event when a phone call is scheduled.

    Args:
        call_id: ID of the scheduled phone call
        call_data: Dict containing call data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="communication.call_scheduled",
        payload={
            "call_id": call_id,
            "call_data": call_data
        },
        key=str(call_id)
    )


def publish_phone_call_completed(
    call_id: int, 
    call_data: Dict[str, Any],
    outcome: Optional[str] = None
) -> bool:
    """Publish an event when a phone call is completed.

    Args:
        call_id: ID of the completed phone call
        call_data: Dict containing call data
        outcome: Optional outcome of the call

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    payload = {
        "call_id": call_id,
        "call_data": call_data
    }
    
    if outcome:
        payload["outcome"] = outcome
        
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="communication.call_completed",
        payload=payload,
        key=str(call_id)
    )