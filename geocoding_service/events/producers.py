"""Producer for geocoding-related Kafka events."""
import logging
from typing import Dict, Any, Optional

from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = RobustKafkaProducer(service_name="geocoding-service")

# Topic for geocoding events
GEOCODING_TOPIC = "geocoding-events"


def publish_distance_result(
    request_id: str,
    result: Dict[str, Any]
) -> bool:
    """Publish an event with distance calculation results.

    Args:
        request_id: ID of the original request
        result: Dict containing distance calculation results

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=GEOCODING_TOPIC,
        event_type="geocoding.distance_result",
        payload={
            "request_id": request_id,
            "result": result
        },
        key=str(request_id)
    )


def publish_geocoding_result(
    request_id: str,
    address: str,
    coordinates: Dict[str, float],
    display_name: Optional[str] = None
) -> bool:
    """Publish an event with geocoding results.

    Args:
        request_id: ID of the original request
        address: Original address that was geocoded
        coordinates: Dict with latitude and longitude
        display_name: Optional formatted address

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=GEOCODING_TOPIC,
        event_type="geocoding.geocode_result",
        payload={
            "request_id": request_id,
            "address": address,
            "coordinates": coordinates,
            "display_name": display_name
        },
        key=str(request_id)
    )


def publish_therapist_search_result(
    request_id: str,
    patient_location: Dict[str, Any],
    therapists: Dict[str, Any],
    search_params: Dict[str, Any]
) -> bool:
    """Publish an event with therapist search results.

    Args:
        request_id: ID of the original request
        patient_location: Location information of the patient
        therapists: Dict containing matching therapists
        search_params: Parameters used for the search

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=GEOCODING_TOPIC,
        event_type="geocoding.therapist_search_result",
        payload={
            "request_id": request_id,
            "patient_location": patient_location,
            "therapists": therapists,
            "search_params": search_params
        },
        key=str(request_id)
    )