"""Email sending utility functions."""
import logging
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any

from flask import current_app
from sqlalchemy import and_, or_, cast, String, func

from shared.utils.database import SessionLocal
from models.email import Email, EmailStatus
from models.email_batch import EmailBatch
from models.phone_call import PhoneCall
from utils.template_renderer import render_template
from utils.phone_call_scheduler import schedule_call_for_email
from shared.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Constants for email batching
MAX_PATIENTS_PER_EMAIL = 5  # Maximum number of patients to include in a single email
MIN_DAYS_BETWEEN_EMAILS = 7  # Minimum days between emails to the same therapist


def get_smtp_settings():
    """Get SMTP settings from app config or use defaults.
    
    Returns:
        dict: SMTP settings
    """
    try:
        # Try to get settings from Flask app config
        return {
            'host': current_app.config.get('SMTP_HOST', config.SMTP_HOST),
            'port': current_app.config.get('SMTP_PORT', config.SMTP_PORT),
            'username': current_app.config.get('SMTP_USERNAME', config.SMTP_USERNAME),
            'password': current_app.config.get('SMTP_PASSWORD', config.SMTP_PASSWORD),
            'use_tls': current_app.config.get('SMTP_USE_TLS', config.SMTP_USE_TLS),
            'sender': current_app.config.get('EMAIL_SENDER', config.EMAIL_SENDER),
            'sender_name': current_app.config.get('EMAIL_SENDER_NAME', config.EMAIL_SENDER_NAME),
        }
    except RuntimeError:
        # Not running in Flask app context, use defaults from config
        return config.get_smtp_settings()