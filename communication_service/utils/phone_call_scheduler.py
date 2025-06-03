"""Phone call scheduling utility functions."""
import logging
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Any

import requests
from sqlalchemy import and_

from shared.utils.database import SessionLocal
from models.phone_call import PhoneCall, PhoneCallStatus, PhoneCallBatch
from models.email import Email, EmailStatus
from shared.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Service URLs from configuration
THERAPIST_SERVICE_URL = config.get_service_url("therapist", internal=True)
MATCHING_SERVICE_URL = config.get_service_url("matching", internal=True)