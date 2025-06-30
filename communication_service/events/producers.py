"""Producer for communication-related Kafka events."""
import logging
from typing import Dict, List, Optional, Any

from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer with robust implementation
try:
    producer = RobustKafkaProducer(service_name="communication-service")
    logger.info("Successfully created shared RobustKafkaProducer")
except Exception as e:
    logger.error(f"ERROR CREATING PRODUCER: {str(e)}")
    import traceback
    traceback.print_exc()

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
    logger.debug(f"Publishing email_created event for email_id={email_id}")
    try:
        result = producer.send_event(
            topic=COMMUNICATION_TOPIC,
            event_type="communication.email_created",
            payload={
                "email_id": email_id,
                "email_data": email_data
            },
            key=str(email_id)
        )
        logger.debug(f"Published email_created event, result={result}")
        return result
    except Exception as e:
        logger.error(f"Error publishing email_created event: {e}", exc_info=True)
        return False


def publish_email_sent(email_id: int, email_data: Dict[str, Any]) -> bool:
    """Publish an event when an email is sent.

    Args:
        email_id: ID of the sent email
        email_data: Dict containing email data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    logger.debug(f"Publishing email_sent event for email_id={email_id}")
    try:
        # PHASE 2: Enhanced payload for letzter_kontakt tracking
        payload = {
            "email_id": email_id,
            "email_data": email_data,
            "communication_type": "email"
        }
        
        # Extract patient_id or therapist_id from email_data if available
        if "patient_id" in email_data:
            payload["patient_id"] = email_data["patient_id"]
        if "therapist_id" in email_data:
            payload["therapist_id"] = email_data["therapist_id"]
        
        result = producer.send_event(
            topic=COMMUNICATION_TOPIC,
            event_type="email.sent",  # Changed to match Phase 2 spec
            payload=payload,
            key=str(email_id)
        )
        logger.debug(f"Published email_sent event, result={result}")
        return result
    except Exception as e:
        logger.error(f"Error publishing email_sent event: {e}", exc_info=True)
        return False


def publish_email_response_received(email_id: int, email_data: Dict[str, Any]) -> bool:
    """Publish an event when an email response is received.
    
    PHASE 2: New function for tracking email responses.

    Args:
        email_id: ID of the email that received a response
        email_data: Dict containing email data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    logger.debug(f"Publishing email_response_received event for email_id={email_id}")
    try:
        payload = {
            "email_id": email_id,
            "email_data": email_data,
            "communication_type": "email"
        }
        
        # Extract patient_id or therapist_id from email_data if available
        if "patient_id" in email_data:
            payload["patient_id"] = email_data["patient_id"]
        if "therapist_id" in email_data:
            payload["therapist_id"] = email_data["therapist_id"]
        
        result = producer.send_event(
            topic=COMMUNICATION_TOPIC,
            event_type="email.response_received",
            payload=payload,
            key=str(email_id)
        )
        logger.debug(f"Published email_response_received event, result={result}")
        return result
    except Exception as e:
        logger.error(f"Error publishing email_response_received event: {e}", exc_info=True)
        return False


def publish_phone_call_scheduled(call_id: int, call_data: Dict[str, Any]) -> bool:
    """Publish an event when a phone call is scheduled.

    Args:
        call_id: ID of the scheduled phone call
        call_data: Dict containing call data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    logger.debug(f"Publishing call_scheduled event for call_id={call_id}")
    try:
        result = producer.send_event(
            topic=COMMUNICATION_TOPIC,
            event_type="communication.call_scheduled",
            payload={
                "call_id": call_id,
                "call_data": call_data
            },
            key=str(call_id)
        )
        logger.debug(f"Published call_scheduled event, result={result}")
        return result
    except Exception as e:
        logger.error(f"Error publishing call_scheduled event: {e}", exc_info=True)
        return False


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
    logger.debug(f"Publishing call_completed event for call_id={call_id}")
    
    # PHASE 2: Enhanced payload for letzter_kontakt tracking
    payload = {
        "call_id": call_id,
        "call_data": call_data,
        "communication_type": "phone_call"
    }
    
    # Extract patient_id or therapist_id from call_data if available
    if "patient_id" in call_data:
        payload["patient_id"] = call_data["patient_id"]
    if "therapist_id" in call_data:
        payload["therapist_id"] = call_data["therapist_id"]
    
    if outcome:
        payload["outcome"] = outcome
    
    try:
        result = producer.send_event(
            topic=COMMUNICATION_TOPIC,
            event_type="phone_call.completed",  # Changed to match Phase 2 spec
            payload=payload,
            key=str(call_id)
        )
        logger.debug(f"Published call_completed event, result={result}")
        return result
    except Exception as e:
        logger.error(f"Error publishing call_completed event: {e}", exc_info=True)
        return False