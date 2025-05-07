"""Robust Kafka producer with retry and queuing capabilities."""
import json
import logging
import os
import time
from datetime import datetime
from threading import Thread, Lock
from typing import Any, Dict, List, Optional, Tuple

from kafka import KafkaProducer as BaseKafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

from shared.kafka.schemas import EventSchema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum number of retries when connecting to Kafka
MAX_CONNECT_RETRIES = 5

# Maximum time to wait between connection attempts (seconds)
MAX_BACKOFF_TIME = 30

# Storage directory for unsent messages
UNSENT_DIR = os.path.join(os.path.dirname(__file__), "unsent")


class RobustKafkaProducer:
    """Robust Kafka producer that can handle connection failures.
    
    Features:
    - Retry connection with exponential backoff
    - Queue messages locally when Kafka is unavailable
    - Background thread for attempting to send queued messages
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "kafka:9092",
        service_name: str = "unknown-service",
        connect_retry: bool = True
    ):
        """Initialize the robust Kafka producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers address
            service_name: Name of the service using this producer
            connect_retry: Whether to retry connecting to Kafka
        """
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        self.producer = None
        self.connected = False
        self.message_queue = []
        self.queue_lock = Lock()
        
        # Create directory for unsent messages if it doesn't exist
        if not os.path.exists(UNSENT_DIR):
            os.makedirs(UNSENT_DIR)
        
        # Try to connect to Kafka, with retry if enabled
        if connect_retry:
            self._connect_with_retry()
        else:
            self._connect()
        
        # Start background thread to process message queue
        self.queue_processor = Thread(
            target=self._process_queue,
            daemon=True
        )
        self.queue_processor.start()
    
    def _connect(self) -> bool:
        """Try to connect to Kafka once.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.producer = BaseKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                # Increase timeouts to be more forgiving
                max_block_ms=10000,  # 10 seconds
                request_timeout_ms=30000,  # 30 seconds
                # Add metadata request timeout
                api_version_auto_timeout_ms=30000,  # 30 seconds
            )
            self.connected = True
            self.logger.info("Successfully connected to Kafka")
            return True
        except (KafkaError, NoBrokersAvailable) as e:
            self.logger.warning(f"Failed to connect to Kafka: {str(e)}")
            self.connected = False
            return False
    
    def _connect_with_retry(self) -> bool:
        """Connect to Kafka with exponential backoff retry.
        
        Returns:
            True if successful, False if all retries failed
        """
        backoff_time = 1  # Start with 1 second backoff
        
        for attempt in range(MAX_CONNECT_RETRIES):
            if self._connect():
                return True
            
            # Calculate next backoff time with exponential increase
            backoff_time = min(backoff_time * 2, MAX_BACKOFF_TIME)
            
            self.logger.info(
                f"Retrying Kafka connection in {backoff_time} seconds "
                f"(attempt {attempt + 1}/{MAX_CONNECT_RETRIES})"
            )
            time.sleep(backoff_time)
        
        self.logger.error(
            f"Failed to connect to Kafka after {MAX_CONNECT_RETRIES} attempts"
        )
        return False
    
    def _store_message(
        self,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        key: Optional[str]
    ) -> None:
        """Store a message to disk when Kafka is unavailable.
        
        Args:
            topic: Kafka topic
            event_type: Type of event
            payload: Event payload
            key: Optional message key
        """
        event = EventSchema(
            event_type=event_type,
            payload=payload,
            producer=self.service_name
        )
        
        message = {
            "topic": topic,
            "key": key,
            "event": event.to_dict()
        }
        
        filename = f"{int(time.time())}_{event.event_id}.json"
        filepath = os.path.join(UNSENT_DIR, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(message, f)
            self.logger.info(
                f"Stored message {event.event_id} to be sent later"
            )
        except Exception as e:
            self.logger.error(f"Failed to store message: {str(e)}")
    
    def _process_queue(self) -> None:
        """Background thread to process the message queue.
        
        This runs continuously, attempting to:
        1. Reconnect to Kafka if disconnected
        2. Send any messages in the in-memory queue
        3. Send any messages stored on disk
        """
        while True:
            # If not connected, try to reconnect
            if not self.connected:
                self._connect()
            
            # If now connected, try to send queued messages
            if self.connected and self.producer:
                # Process in-memory queue first
                with self.queue_lock:
                    pending_messages = self.message_queue.copy()
                    self.message_queue = []
                
                for topic, key, event_dict in pending_messages:
                    try:
                        key_bytes = key.encode('utf-8') if key else None
                        future = self.producer.send(
                            topic,
                            value=event_dict,
                            key=key_bytes
                        )
                        future.get(timeout=10)
                        self.logger.info(
                            f"Sent queued message to {topic}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to send queued message: {str(e)}"
                        )
                        # Put back in queue
                        with self.queue_lock:
                            self.message_queue.append((topic, key, event_dict))
                
                # Process messages stored on disk
                if os.path.exists(UNSENT_DIR):
                    for filename in os.listdir(UNSENT_DIR):
                        if not filename.endswith('.json'):
                            continue
                        
                        filepath = os.path.join(UNSENT_DIR, filename)
                        try:
                            with open(filepath, 'r') as f:
                                message = json.load(f)
                            
                            topic = message["topic"]
                            key = message["key"]
                            event_dict = message["event"]
                            
                            key_bytes = key.encode('utf-8') if key else None
                            future = self.producer.send(
                                topic,
                                value=event_dict,
                                key=key_bytes
                            )
                            future.get(timeout=10)
                            
                            # If successful, delete the file
                            os.remove(filepath)
                            self.logger.info(
                                f"Sent stored message from {filepath}"
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Failed to send stored message {filepath}: {str(e)}"
                            )
            
            # Sleep before next attempt
            time.sleep(5)
    
    def send_event(
        self,
        topic: str,
        event_type: str,
        payload: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """Send an event to Kafka using the standard event schema.
        
        If Kafka is unavailable, the message will be queued for later.
        
        Args:
            topic: Kafka topic to send the event to
            event_type: Type of event (e.g., patient.created)
            payload: Event data payload
            key: Optional message key (for partitioning)
            
        Returns:
            True if sent immediately, False if queued
        """
        event = EventSchema(
            event_type=event_type,
            payload=payload,
            producer=self.service_name
        )
        
        # If not connected, queue the message
        if not self.connected or self.producer is None:
            with self.queue_lock:
                self.message_queue.append((topic, key, event.to_dict()))
            self._store_message(topic, event_type, payload, key)
            self.logger.info(
                f"Queued event {event_type} for later sending to topic {topic}"
            )
            return False
        
        # If connected, try to send immediately
        try:
            key_bytes = key.encode('utf-8') if key else None
            future = self.producer.send(
                topic,
                value=event.to_dict(),
                key=key_bytes
            )
            future.get(timeout=10)
            self.logger.info(
                f"Event {event_type} sent to topic {topic}",
                extra={"event_id": event.event_id}
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to send event {event_type} to topic {topic}: {str(e)}",
                extra={"event_id": event.event_id}
            )
            # Queue for retry
            with self.queue_lock:
                self.message_queue.append((topic, key, event.to_dict()))
            self._store_message(topic, event_type, payload, key)
            return False
    
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.close()
            self.connected = False