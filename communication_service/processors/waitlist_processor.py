"""Waitlist verification email processor."""
import logging
import os
from typing import Dict, Any, Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

import requests
from shared.config import get_config

logger = logging.getLogger(__name__)


class WaitlistProcessor:
    """Process waitlist verification email requests."""

    def __init__(self):
        """Initialize the waitlist processor."""
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

        logger.info("WaitlistProcessor initialized")

    def process_waitlist_verification(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process a waitlist verification email request.

        Args:
            data: Waitlist verification data from JSON file (with HMAC already verified)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Extract data from nested structure
            # Structure: data.data.email, data.data.token, etc.
            waitlist_data = data.get('data', {})

            # Required fields
            email = waitlist_data.get('email')
            language = waitlist_data.get('language', 'en')  # Default to English
            verification_link = waitlist_data.get('verification_link')

            if not all([email, verification_link]):
                return False, "Missing required fields: email or verification_link"

            # Validate language
            if language not in ['en', 'de']:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = 'en'

            # Get appropriate subject
            if language == 'de':
                subject = waitlist_data.get('subject_de', 'Curavani: Bestätigen Sie Ihre Virtual Coach Wartelisten-Anmeldung')
            else:
                subject = waitlist_data.get('subject_en', 'Curavani: Confirm Your Virtual Coach Waitlist Registration')

            # Optional fields with defaults
            expiry_minutes = waitlist_data.get('expiry_minutes', 30)

            # Prepare template context
            context = {
                'verification_link': verification_link,
                'expiry_minutes': expiry_minutes,
                'current_year': datetime.now().year
            }

            # Select template based on language
            template_name = f'waitlist_verification_{language}.md'

            # Render template
            try:
                template = self.env.get_template(template_name)
                email_content = template.render(context)
            except Exception as e:
                logger.error(f"Template rendering failed for {template_name}: {str(e)}")
                # Fall back to simple text based on language
                if language == 'de':
                    email_content = f"""
Hallo,

vielen Dank für Ihr Interesse an Virtual Coach von Curavani!

Bitte bestätigen Sie Ihre E-Mail-Adresse:
{verification_link}

Dieser Link ist {expiry_minutes} Minuten gültig.

Beste Grüße,
Ihr Curavani-Team
                    """.strip()
                else:
                    email_content = f"""
Hello,

Thank you for your interest in Virtual Coach by Curavani!

Please confirm your email address:
{verification_link}

This link is valid for {expiry_minutes} minutes.

Best regards,
The Curavani Team
                    """.strip()

            # Send via system-messages endpoint (no database storage)
            try:
                response = requests.post(
                    f"{self.comm_service_url}/api/system-messages",
                    json={
                        'subject': subject,
                        'message': email_content,
                        'recipient_email': email,
                        'recipient_name': '',  # No name available at this stage
                        'sender_name': self.config.EMAIL_SENDER_NAME or 'Curavani',
                        'process_markdown': True,  # Process markdown to HTML
                        'add_legal_footer': True   # Add legal footer
                    },
                    timeout=10
                )

                if response.ok:
                    result = response.json()
                    logger.info(f"Waitlist verification email sent successfully to {email} in {language}")
                    return True, f"Waitlist verification email sent to: {result.get('recipient')}"
                else:
                    error_msg = f"Failed to send email: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, error_msg

            except requests.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error processing waitlist verification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
