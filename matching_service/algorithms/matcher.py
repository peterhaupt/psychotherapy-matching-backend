"""Matching algorithm implementation for the Matching Service."""
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple

from shared.utils.database import SessionLocal
from models.placement_request import PlacementRequest, PlacementRequestStatus
from shared.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Service URLs from configuration
PATIENT_SERVICE_URL = config.get_service_url("patient", internal=True)
THERAPIST_SERVICE_URL = config.get_service_url("therapist", internal=True)
GEOCODING_SERVICE_URL = config.get_service_url("geocoding", internal=True)