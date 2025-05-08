"""Robust Kafka producer with retry and queuing capabilities."""
import json
import logging
import time
from threading import Thread

from kafka import KafkaProducer as BaseKafkaProducer
from kafka.errors import KafkaError

from shared.kafka.schemas import EventSchema

class RobustKafkaProducer:
    """Kafka producer with connection retry and message queuing."""
    
    def __init__(
        self,
        bootstrap_servers = "kafka:9092",
        service_name = "unknown-service"
    ):
        """Initialize the robust Kafka producer."""
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        self.producer = None
        self.connected = False
        self.message_queue = []
        
        # Try to connect without blocking startup
        self._connect()
        
        # Start background thread for reconnection and queue processing
        self.queue_processor = Thread(
            target=self._process_queue,
            daemon=True
        )
        self.queue_processor.start()
        
    def _connect(self):
        """Try to connect to Kafka once."""
        try:
            self.producer = BaseKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.connected = True
            self.logger.info("Successfully connected to Kafka")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to connect to Kafka: {str(e)}")
            self.connected = False
            return False
    
    def _process_queue(self):
        """Background thread to process the message queue."""
        retry_delay = 1  # Start with 1 second delay
        
        while True:
            # If not connected, try to reconnect
            if not self.connected:
                if self._connect():
                    retry_delay = 1  # Reset delay on successful connection
                else:
                    # Exponential backoff with cap
                    retry_delay = min(retry_delay * 2, 30)
                    time.sleep(retry_delay)
                    continue
            
            # If connected, try to send queued messages
            if self.connected and self.producer:
                if self.message_queue:
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
                            self.message_queue.append((topic, key, event_dict))
                            
                            # Reconnect if there was a connection error
                            if isinstance(e, KafkaError):
                                self.connected = False
                                break
            
            # Sleep before next attempt
            time.sleep(5)
    
    def send_event(self, topic, event_type, payload, key=None):
        """Send an event to Kafka using the standard event schema."""
        event = EventSchema(
            event_type=event_type,
            payload=payload,
            producer=self.service_name
        )
        
        # If not connected, queue the message
        if not self.connected or self.producer is None:
            self.message_queue.append((topic, key, event.to_dict()))
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
                f"Event {event_type} sent to topic {topic}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to send event {event_type} to topic {topic}: {str(e)}"
            )
            # Queue for retry
            self.message_queue.append((topic, key, event.to_dict()))
            
            # Mark as disconnected if it was a Kafka error
            if isinstance(e, KafkaError):
                self.connected = False
                
            return False