"""Producer for patient-related Kafka events."""
import logging
from typing import Dict, Any, Optional

from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = RobustKafkaProducer(service_name="patient-service")

# Topic for patient events
PATIENT_TOPIC = "patient-events"


def publish_patient_created(patient_id: int, patient_data: Dict[str, Any]) -> bool:
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


def publish_patient_updated(patient_id: int, patient_data: Dict[str, Any]) -> bool:
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


def publish_patient_deleted(patient_id: int, additional_data: Optional[Dict[str, Any]] = None) -> bool:
    """Publish an event when a patient is deleted.

    Args:
        patient_id: ID of the deleted patient
        additional_data: Optional additional data about the deletion

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    payload = {"patient_id": patient_id}
    if additional_data:
        payload.update(additional_data)
    
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.deleted",
        payload=payload,
        key=str(patient_id)
    )


def publish_patient_status_changed(
    patient_id: int, 
    old_status: Optional[str], 
    new_status: Optional[str], 
    patient_data: Dict[str, Any]
) -> bool:
    """Publish an event when a patient's status changes.

    Args:
        patient_id: ID of the patient
        old_status: Previous status value
        new_status: New status value
        patient_data: Dict containing updated patient data

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.status_changed",
        payload={
            "patient_id": patient_id,
            "old_status": old_status,
            "new_status": new_status,
            "patient_data": patient_data
        },
        key=str(patient_id)
    )


def publish_patient_excluded_therapist(
    patient_id: int, 
    therapist_id: int, 
    reason: Optional[str] = None
) -> bool:
    """Publish an event when a patient excludes a therapist.

    Args:
        patient_id: ID of the patient
        therapist_id: ID of the excluded therapist
        reason: Optional reason for exclusion

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.therapist_excluded",
        payload={
            "patient_id": patient_id,
            "therapist_id": therapist_id,
            "reason": reason
        },
        key=str(patient_id)
    )
