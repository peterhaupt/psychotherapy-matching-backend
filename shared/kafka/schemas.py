"""Standard Kafka event schemas for the therapy platform."""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


class EventSchema:
    """Standard event schema for Kafka messages."""

    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        producer: str,
        event_id: Optional[str] = None,
        version: str = "1.0"
    ):
        """Initialize a new event schema.

        Args:
            event_type: Type of event (e.g., patient.created)
            payload: Event payload data
            producer: Service that produced the event
            event_id: Optional UUID for the event (generated if not provided)
            version: Schema version
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.version = version
        self.timestamp = datetime.utcnow().isoformat()
        self.producer = producer
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary format.

        Returns:
            Dict representation of the event
        """
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "version": self.version,
            "timestamp": self.timestamp,
            "producer": self.producer,
            "payload": self.payload
        }

    def to_json(self) -> str:
        """Serialize the event to JSON.

        Returns:
            JSON string representation of the event
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'EventSchema':
        """Deserialize JSON to an EventSchema object.

        Args:
            json_str: JSON string to deserialize

        Returns:
            EventSchema object created from the JSON data
        """
        data = json.loads(json_str)
        event = cls(
            event_type=data["eventType"],
            payload=data["payload"],
            producer=data["producer"],
            event_id=data["eventId"],
            version=data["version"]
        )
        event.timestamp = data["timestamp"]
        return event