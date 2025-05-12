"""Configuration settings for the Communication Service."""
import os

# Default SMTP settings
SMTP_HOST = os.environ.get("SMTP_HOST", "127.0.0.1")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "therapieplatz@peterhaupt.de")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "***REMOVED_EXPOSED_PASSWORD***")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "True").lower() == "true"

# Email sender defaults
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "therapieplatz@peterhaupt.de")
EMAIL_SENDER_NAME = os.environ.get("EMAIL_SENDER_NAME", "Boona Therapieplatz-Vermittlung")

# Application settings
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
DATABASE_URI = os.environ.get(
    "DATABASE_URI", 
    "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"
)