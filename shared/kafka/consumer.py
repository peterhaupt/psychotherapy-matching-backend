"""Kafka consumer for the therapy platform."""
import json
import logging
from typing import Callable, List, Optional

from kafka import KafkaConsumer as BaseKafkaConsumer
from kafka.errors import KafkaError

from .schemas import EventSchema


class KafkaConsumer:
    """Wrapper for Kafka consumer with standardized event handling."""

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: str = "kafka:9092",
        auto_offset_reset: str = "earliest"
    ):
        """Initialize the Kafka consumer.

        Args:
            topics: List of Kafka topics to subscribe to
            group_id: Consumer group ID
            bootstrap_servers: Kafka bootstrap servers address
            auto_offset_reset: Offset reset strategy
        """
        self.topics = topics
        self.group_id = group_id
        self.logger = logging.getLogger(__name__)

        try:
            self.consumer = BaseKafkaConsumer(
                *topics,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
        except KafkaError as e:
            self.logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise

    def process_events(
        self,
        handler: Callable[[EventSchema], None],
        event_types: Optional[List[str]] = None,
        timeout_ms: int = 1000
    ):
        """Process events from subscribed topics.

        Args:
            handler: Function to call for each message
            event_types: Optional list of event types to process
            timeout_ms: Poll timeout in milliseconds
        """
        try:
            for message in self.consumer:
                try:
                    # Extract value and convert to EventSchema
                    event_data = message.value

                    # Skip if event_types
                    # is specified and this type is not included
                    if (event_types and
                            "eventType" in event_data and
                            event_data["eventType"] not in event_types):
                        continue

                    event = EventSchema(
                        event_type=event_data["eventType"],
                        payload=event_data["payload"],
                        producer=event_data["producer"],
                        event_id=event_data["eventId"],
                        version=event_data["version"]
                    )

                    # Process the event
                    handler(event)

                    # Commit offset after successful processing
                    self.consumer.commit()

                except Exception as e:
                    self.logger.error(
                        f"Error processing event: {str(e)}",
                        extra={
                            "topic": message.topic,
                            "partition": message.partition
                        }
                    )
        except KafkaError as e:
            self.logger.error(f"Kafka error during consumption: {str(e)}")
        except Exception as e:
            self.logger.error(
                f"Unexpected error during event processing: {str(e)}"
            )

    def close(self):
        """Close the Kafka consumer."""
        self.consumer.close()
