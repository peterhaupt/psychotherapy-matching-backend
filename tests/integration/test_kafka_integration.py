"""Test script for Kafka integration with Patient Service."""
import json
import logging
import sys
from argparse import ArgumentParser

from kafka import KafkaConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def listen_for_events(topic, timeout=60):
    """Listen for events on a Kafka topic and print them.

    Args:
        topic: Kafka topic to listen to
        timeout: Time in seconds to listen before exiting
    """
    logger.info(f"Listening for events on topic '{topic}' for {timeout} seconds")
    
    # Create consumer
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers='localhost:9092',
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=timeout * 1000
    )
    
    # Listen for messages
    events_received = 0
    try:
        for message in consumer:
            events_received += 1
            event_data = message.value
            logger.info(f"Received event: {event_data['eventType']}")
            logger.info(f"Event details: {event_data}")
            logger.info("---")
    except KeyboardInterrupt:
        logger.info("Listening interrupted by user")
    finally:
        consumer.close()
    
    logger.info(f"Listening complete. Received {events_received} events.")
    return events_received


def main():
    """Run the Kafka integration test."""
    parser = ArgumentParser(description="Test Kafka integration with Patient Service")
    parser.add_argument(
        '--topic',
        default='patient-events',
        help='Kafka topic to listen to (default: patient-events)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Time in seconds to listen for events (default: 60)'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Kafka integration test")
    logger.info(
        "In another terminal, use the Patient Service API to create, "
        "update, or delete patients"
    )
    
    events_received = listen_for_events(args.topic, args.timeout)
    
    if events_received > 0:
        logger.info("Test PASSED! ✅ Events were successfully published and received.")
        return 0
    else:
        logger.error(
            "Test FAILED! ❌ No events were received. "
            "Check your Kafka configuration and event publishing code."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())