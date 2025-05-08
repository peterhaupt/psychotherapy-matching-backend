"""Producer for patient-related Kafka events."""
import logging
from typing import Dict, Any

from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = RobustKafkaProducer(service_name="patient-service")

# Topic for patient events
PATIENT_TOPIC = "patient-events"


def publish_patient_created(patient_id: int, patient_data: Dict[str, Any]) -> bool:  # noqa: E501
    """Publish an event when a new patient is created.

    Args:
        patient_id: ID of the created patient
        patient_data: Dict containing patient data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.created",
        payload={
            "patient_id": patient_id,
            "patient_data": patient_data
        },
        key=str(patient_id)
    )


def publish_patient_updated(patient_id: int, patient_data: Dict[str, Any]) -> bool:  # noqa: E501
    """Publish an event when a patient is updated.

    Args:
        patient_id: ID of the updated patient
        patient_data: Dict containing updated patient data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.updated",
        payload={
            "patient_id": patient_id,
            "patient_data": patient_data
        },
        key=str(patient_id)
    )


def publish_patient_deleted(patient_id: int) -> bool:
    """Publish an event when a patient is deleted.

    Args:
        patient_id: ID of the deleted patient

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.deleted",
        payload={
            "patient_id": patient_id
        },
        key=str(patient_id)
    )
