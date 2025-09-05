"""Verification email processor."""
import logging
import os
from typing import Dict, Any, Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

import requests
from shared.config import get_config

logger = logging.getLogger(__name__)


class VerificationProcessor:
    """Process verification email requests."""
    
    def __init__(self):
        """Initialize the verification processor."""
        self.config = get_config()
        self.comm_service_url = self.config.get_service_url('communication', internal=True)
        
        # Set up Jinja2 environment for templates
        # In Docker container, shared is mounted at /app/shared
        if os.path.exists('/app/shared'):
            shared_path = '/app/shared'
        else:
            # Local development - go up from communication_service to project root
            shared_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared')
        
        template_dir = os.path.join(shared_path, 'templates', 'emails')
        
        if not os.path.exists(template_dir):
            logger.warning(f"Template directory not found: {template_dir}")
            # Create a basic environment anyway
            self.env = Environment()
        else:
            self.env = Environment(loader=FileSystemLoader(template_dir))
        
        logger.info("VerificationProcessor initialized")
    
    def process_verification(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process a verification email request.
        
        Args:
            data: Verification data from JSON file (with HMAC already verified)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Extract data from nested structure
            # Structure: data.data.email, data.data.token, etc.
            verification_data = data.get('data', {})
            
            # Required fields
            email = verification_data.get('email')
            token = verification_data.get('token')
            verification_link = verification_data.get('verification_link')
            
            if not all([email, token, verification_link]):
                return False, "Missing required fields: email, token, or verification_link"
            
            # Optional fields with defaults
            subject = verification_data.get('subject', 'Bestätigen Sie Ihre E-Mail-Adresse | Curavani')
            expiry_minutes = verification_data.get('expiry_minutes', 30)
            
            # Prepare template context
            context = {
                'verification_link': verification_link,
                'expiry_minutes': expiry_minutes,
                'current_year': datetime.now().year
            }
            
            # Render template
            try:
                template = self.env.get_template('verification_email.md')
                email_content = template.render(context)
            except Exception as e:
                logger.error(f"Template rendering failed: {str(e)}")
                # Fall back to simple text
                email_content = f"""
Vielen Dank für Ihre Registrierung bei Curavani!

Bitte bestätigen Sie Ihre E-Mail-Adresse:
{verification_link}

Dieser Link ist {expiry_minutes} Minuten gültig.

Mit freundlichen Grüßen
Ihr Curavani Team
                """.strip()
            
            # Create email via communication service API
            email_data = {
                'patient_id': None,  # No patient exists yet
                'betreff': subject,
                'inhalt_markdown': email_content,
                'empfaenger_email': email,
                'empfaenger_name': '',  # No name available at this stage
                'absender_email': self.config.EMAIL_SENDER or 'info@curavani.com',
                'absender_name': self.config.EMAIL_SENDER_NAME or 'Curavani',
                'add_legal_footer': True,
                'status': 'In_Warteschlange'  # Queue for immediate sending
            }
            
            # Send request to internal email API
            try:
                response = requests.post(
                    f"{self.comm_service_url}/api/emails",
                    json=email_data,
                    timeout=10
                )
                
                if response.ok:
                    result = response.json()
                    logger.info(f"Verification email queued successfully for {email}")
                    return True, f"Verification email created with ID: {result.get('id')}"
                else:
                    error_msg = f"Failed to create email: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, error_msg
                    
            except requests.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error processing verification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg