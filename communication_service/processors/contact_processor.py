"""Contact form processor for forwarding to support."""
import logging
import os
from typing import Dict, Any, Tuple
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

import requests
from shared.config import get_config

logger = logging.getLogger(__name__)


class ContactProcessor:
    """Process contact form submissions."""
    
    def __init__(self):
        """Initialize the contact processor."""
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
        
        logger.info("ContactProcessor initialized")
    
    def process_contact(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Process a contact form submission.
        
        Args:
            data: Contact form data from JSON file (with HMAC already verified)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Handle the nested structure: data.data.data.form_data
            # This is because of HMAC wrapper + PHP's double nesting
            contact_wrapper = data.get('data', {})
            
            # Check if we have the expected nested structure
            if 'data' in contact_wrapper:
                # Double nested structure (as in the example)
                inner_data = contact_wrapper.get('data', {})
                form_data = inner_data.get('form_data', {})
                metadata = inner_data.get('metadata', {})
                support_email = inner_data.get('support_email', 'patienten@curavani.com')
                source = inner_data.get('source', 'curavani.com')
            else:
                # Simpler structure (fallback)
                form_data = contact_wrapper.get('form_data', {})
                metadata = contact_wrapper.get('metadata', {})
                support_email = contact_wrapper.get('support_email', 'patienten@curavani.com')
                source = contact_wrapper.get('source', 'curavani.com')
            
            # Extract form fields
            vorname = form_data.get('vorname', '')
            nachname = form_data.get('nachname', '')
            email = form_data.get('email', '')
            telefon = form_data.get('telefon', '')
            nachricht = form_data.get('nachricht', '')
            form_submitted_at = form_data.get('form_submitted_at', '')
            
            # Validate required fields
            if not all([vorname, nachname, email]):
                return False, f"Missing required fields. Got: vorname={bool(vorname)}, nachname={bool(nachname)}, email={bool(email)}"
            
            # Extract metadata
            ip_address = metadata.get('ip_address', 'unknown')
            request_id = metadata.get('request_id', 'unknown')
            environment = data.get('environment', 'unknown')
            
            # Prepare template context
            context = {
                'vorname': vorname,
                'nachname': nachname,
                'email': email,
                'telefon': telefon,
                'nachricht': nachricht,
                'form_submitted_at': form_submitted_at,
                'source': source,
                'ip_address': ip_address,
                'request_id': request_id,
                'environment': environment
            }
            
            # Render template
            try:
                template = self.env.get_template('contact_form_forward.md')
                email_content = template.render(context)
            except Exception as e:
                logger.error(f"Template rendering failed: {str(e)}")
                # Fall back to simple text
                email_content = f"""
Neue Kontaktformular-Nachricht

Name: {vorname} {nachname}
E-Mail: {email}
Telefon: {telefon}

Nachricht:
{nachricht if nachricht else '(Keine Nachricht eingegeben)'}

---
Zeitpunkt: {form_submitted_at}
IP: {ip_address}
Request-ID: {request_id}
Umgebung: {environment}
                """.strip()
            
            # Create email subject with sender name
            subject = f"[Kontaktformular] Anfrage von {vorname} {nachname}"
            
            # Create email via communication service API
            email_data = {
                'patient_id': None,  # Contact forms don't have patient IDs
                'betreff': subject,
                'inhalt_markdown': email_content,
                'empfaenger_email': support_email,
                'empfaenger_name': 'Curavani Support',
                'absender_email': self.config.EMAIL_SENDER or 'info@curavani.com',
                'absender_name': f"{vorname} {nachname} (via Kontaktformular)",
                'add_legal_footer': False,  # No legal footer for internal emails
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
                    logger.info(f"Contact form forwarded successfully from {email} to {support_email}")
                    return True, f"Contact form email created with ID: {result.get('id')}"
                else:
                    error_msg = f"Failed to create email: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return False, error_msg
                    
            except requests.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error processing contact: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg