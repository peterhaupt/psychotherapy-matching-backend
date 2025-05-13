"""Consumer for Kafka events in the Geocoding Service."""
import json
import logging
import threading
from typing import Dict, Any, Optional

from shared.kafka import EventSchema, KafkaConsumer
from utils.distance import calculate_distance
from events.producers import publish_distance_result

# Initialize logging
logger = logging.getLogger(__name__)


def handle_geocoding_request(event: EventSchema) -> None:
    """Handle geocoding request events.

    Args:
        event: The event to process
    """
    logger.info(
        f"Processing geocoding event: {event.event_type}",
        extra={"event_id": event.event_id}
    )

    # Handle different event types
    if event.event_type == "geocoding.calculate_distance":
        process_distance_calculation(event)


def process_distance_calculation(event: EventSchema) -> None:
    """Process a distance calculation request.
    
    Args:
        event: The event containing distance calculation request
    """
    try:
        # Extract request parameters
        payload = event.payload
        request_id = payload.get("request_id")
        
        # Check that we have both origin and destination
        origin = payload.get("origin")
        destination = payload.get("destination")
        travel_mode = payload.get("travel_mode", "car")
        
        if not origin or not destination:
            logger.error(
                f"Missing origin or destination in request {request_id}"
            )
            return
            
        # Calculate distance
        result = calculate_distance(
            origin, destination, travel_mode=travel_mode
        )
        
        # Add request ID to result
        result["request_id"] = request_id
        
        # Publish result
        publish_distance_result(request_id, result)
        
        logger.info(
            f"Processed distance calculation for request {request_id}: "
            f"{result['distance_km']} km"
        )
    except Exception as e:
        logger.error(
            f"Error processing distance calculation: {str(e)}",
            exc_info=True
        )


def start_consumers():
    """Start all Kafka consumers for the Geocoding Service."""
    try:
        # Consumer for geocoding requests
        geocoding_consumer = KafkaConsumer(
            topics=["geocoding-requests"],
            group_id="geocoding-service",
        )
        
        # Define the geocoding event types we're interested in
        geocoding_event_types = [
            "geocoding.calculate_distance",
            "geocoding.search_therapists"
        ]
        
        # Start processing in a separate thread
        geocoding_thread = threading.Thread(
            target=geocoding_consumer.process_events,
            args=(handle_geocoding_request, geocoding_event_types),
            daemon=True
        )
        geocoding_thread.start()
        
        logger.info("Kafka consumers initialized")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")