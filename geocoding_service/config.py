"""Configuration settings for the Geocoding Service."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Database configuration
DATABASE_URI = os.environ.get(
    "DATABASE_URI", 
    "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"
)
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

# OpenStreetMap Nominatim API configuration
OSM_API_URL = os.environ.get(
    "OSM_API_URL", 
    "https://nominatim.openstreetmap.org"
)
OSM_USER_AGENT = os.environ.get(
    "OSM_USER_AGENT", 
    "BonaTherapyPlatform/1.0"
)
OSM_TIMEOUT = int(os.environ.get("OSM_TIMEOUT", "10"))
OSM_MAX_RETRIES = int(os.environ.get("OSM_MAX_RETRIES", "3"))

# Rate limiting for API calls (requests per second)
OSM_RATE_LIMIT = float(os.environ.get("OSM_RATE_LIMIT", "1.0"))

# OpenStreetMap OSRM API configuration (for routing)
OSRM_API_URL = os.environ.get(
    "OSRM_API_URL", 
    "https://router.project-osrm.org"
)
OSRM_PROFILE_CAR = os.environ.get("OSRM_PROFILE_CAR", "car")
OSRM_PROFILE_TRANSIT = os.environ.get("OSRM_PROFILE_TRANSIT", "foot")

# Geocoding cache settings
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "2592000"))  # 30 days default
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "1000"))

# Service configuration
SERVICE_PORT = int(os.environ.get("SERVICE_PORT", "8005"))