"""Kafka producer for the therapy platform."""
import json
import logging
from typing import Any, Dict, Optional

from kafka import KafkaProducer as BaseKafkaProducer
from kafka.errors import KafkaError

from .schemas import EventSchema


class KafkaProducer:
    """Wrapper for Kafka producer with standardized event handling."""

    def __init__(
        self,
        bootstrap_servers: str = "kafka:9092",
        service_name: str = "unknown-service"
    ):
        """Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers address
            service_name: Name of the service using this producer
        """
        self.producer = BaseKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)

    def send_event(
        self,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """Send an event to Kafka using the standard event schema.

        Args:
            topic: Kafka topic to send the event to
            event_type: Type of event (e.g., patient.created)
            payload: Event data payload
            key: Optional message key (for partitioning)

        Returns:
            True if successful, False otherwise
        """
        event = EventSchema(
            event_type=event_type,
            payload=payload,
            producer=self.service_name
        )

        try:
            # Convert key to bytes if provided
            key_bytes = key.encode('utf-8') if key else None

            # Send and get the future
            future = self.producer.send(
                topic,
                value=event.to_dict(),
                key=key_bytes
            )

            # Wait for the send to complete
            future.get(timeout=10)
            self.logger.info(
                f"Event {event_type} sent to topic {topic}",
                extra={"event_id": event.event_id}
            )
            return True
        except KafkaError as e:
            self.logger.error(
                f"Failed to send event {event_type} \
                    to topic {topic}: {str(e)}",
                extra={"event_id": event.event_id}
            )
            return False

    def close(self):
        """Close the Kafka producer."""
        self.producer.close()
