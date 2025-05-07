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

# Configure logging
logger = logging.getLogger(__name__)

# Default SMTP settings (will be overridden by app config if available)
DEFAULT_SMTP_HOST = "127.0.0.1"
DEFAULT_SMTP_PORT = 1025
DEFAULT_SMTP_USERNAME = "therapieplatz@peterhaupt.de"
DEFAULT_SMTP_PASSWORD = "***REMOVED_EXPOSED_PASSWORD***"
DEFAULT_SMTP_USE_TLS = True
DEFAULT_SENDER = "therapieplatz@peterhaupt.de"
DEFAULT_SENDER_NAME = "Boona Therapieplatz-Vermittlung"

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
            'host': current_app.config.get('SMTP_HOST', DEFAULT_SMTP_HOST),
            'port': current_app.config.get('SMTP_PORT', DEFAULT_SMTP_PORT),
            'username': current_app.config.get('SMTP_USERNAME', DEFAULT_SMTP_USERNAME),
            'password': current_app.config.get('SMTP_PASSWORD', DEFAULT_SMTP_PASSWORD),
            'use_tls': current_app.config.get('SMTP_USE_TLS', DEFAULT_SMTP_USE_TLS),
            'sender': current_app.config.get('EMAIL_SENDER', DEFAULT_SENDER),
            'sender_name': current_app.config.get('EMAIL_SENDER_NAME', DEFAULT_SENDER_NAME),
        }
    except RuntimeError:
        # Not running in Flask app context, use defaults
        return {
            'host': DEFAULT_SMTP_HOST,
            'port': DEFAULT_SMTP_PORT,
            'username': DEFAULT_SMTP_USERNAME,
            'password': DEFAULT_SMTP_PASSWORD,
            'use_tls': DEFAULT_SMTP_USE_TLS,
            'sender': DEFAULT_SENDER,
            'sender_name': DEFAULT_SENDER_NAME,
        }


def can_contact_therapist(therapist_id: int) -> bool:
    """Check if a therapist can be contacted based on 7-day rule.
    
    Args:
        therapist_id: ID of the therapist to check
        
    Returns:
        bool: True if the therapist can be contacted, False otherwise
    """
    db = SessionLocal()
    try:
        # Calculate the date 7 days ago
        seven_days_ago = datetime.utcnow() - timedelta(days=MIN_DAYS_BETWEEN_EMAILS)
        
        # Check for any emails sent to this therapist in the last 7 days
        recent_email = db.query(Email).filter(
            Email.therapist_id == therapist_id,
            Email.sent_at >= seven_days_ago,
            Email.status == EmailStatus.SENT
        ).first()
        
        # Check for any scheduled phone calls to this therapist in the next 7 days
        future_call = db.query(PhoneCall).filter(
            PhoneCall.therapist_id == therapist_id,
            PhoneCall.scheduled_date >= datetime.utcnow().date(),
            PhoneCall.scheduled_date <= (datetime.utcnow() + timedelta(days=7)).date()
        ).first()
        
        # Can contact if no recent emails and no upcoming calls
        return recent_email is None and future_call is None
    except Exception as e:
        logger.error(f"Error checking therapist contact eligibility: {str(e)}")
        return False  # Default to not contacting if there's an error
    finally:
        db.close()


def create_batch_email(
    therapist_id: int,
    placement_request_ids: List[int],
    priority_order: Optional[List[int]] = None
) -> Optional[int]:
    """Create a batch email for multiple placement requests.
    
    Args:
        therapist_id: ID of the therapist to contact
        placement_request_ids: List of placement request IDs to include
        priority_order: Optional list of IDs in priority order
        
    Returns:
        Optional[int]: ID of the created email or None if creation failed
    """
    if not placement_request_ids:
        return None
        
    # Respect MAX_PATIENTS_PER_EMAIL limit
    if len(placement_request_ids) > MAX_PATIENTS_PER_EMAIL:
        # If priority_order is provided, use it to select top requests
        if priority_order:
            # Filter placement_request_ids to only include those in priority_order
            # and take the top MAX_PATIENTS_PER_EMAIL
            prioritized_ids = [
                pr_id for pr_id in priority_order 
                if pr_id in placement_request_ids
            ][:MAX_PATIENTS_PER_EMAIL]
            
            # If we have enough prioritized IDs, use them
            if len(prioritized_ids) >= MAX_PATIENTS_PER_EMAIL:
                placement_request_ids = prioritized_ids
            else:
                # Otherwise, take the remaining slots from the original list
                # but exclude those already in prioritized_ids
                remaining_ids = [
                    pr_id for pr_id in placement_request_ids 
                    if pr_id not in prioritized_ids
                ]
                placement_request_ids = (
                    prioritized_ids + 
                    remaining_ids[:MAX_PATIENTS_PER_EMAIL - len(prioritized_ids)]
                )
        else:
            # Without priority order, just take the first MAX_PATIENTS_PER_EMAIL
            placement_request_ids = placement_request_ids[:MAX_PATIENTS_PER_EMAIL]
    
    db = SessionLocal()
    try:
        # Get therapist data
        therapist_result = db.execute(
            """
            SELECT anrede, titel, vorname, nachname, email 
            FROM therapist_service.therapists 
            WHERE id = :therapist_id
            """,
            {"therapist_id": therapist_id}
        ).fetchone()
        
        if not therapist_result:
            logger.error(f"Therapist {therapist_id} not found")
            return None
            
        # Extract therapist data
        therapist_data = {
            'anrede': therapist_result[0],
            'titel': therapist_result[1],
            'vorname': therapist_result[2],
            'nachname': therapist_result[3],
            'email': therapist_result[4]
        }
        
        # Get placement request data
        placement_requests = db.execute(
            """
            SELECT pr.id, p.diagnose, p.geschlecht, p.zeitliche_verfuegbarkeit, 
                   p.beschwerden_seit, p.offen_fuer_gruppentherapie,
                   p.psychotherapieerfahrung, p.aktuelle_psychische_beschwerden
            FROM matching_service.placement_requests pr
            JOIN patient_service.patients p ON pr.patient_id = p.id
            WHERE pr.id IN :request_ids
            """,
            {"request_ids": tuple(placement_request_ids)}
        ).fetchall()
        
        if not placement_requests:
            logger.error(f"No placement requests found for IDs: {placement_request_ids}")
            return None
            
        # Prepare patient data for template
        patients_data = []
        for pr in placement_requests:
            zeitliche_verfuegbarkeit = pr[3] or {}
            weekdays = {
                'monday': 'Montag',
                'tuesday': 'Dienstag',
                'wednesday': 'Mittwoch',
                'thursday': 'Donnerstag',
                'friday': 'Freitag',
                'saturday': 'Samstag',
                'sunday': 'Sonntag'
            }
            
            # Format availability text
            zeitliche_verfuegbarkeit_text = ""
            for day, times in zeitliche_verfuegbarkeit.items():
                if day in weekdays and times:
                    day_name = weekdays[day]
                    time_slots = []
                    for time_slot in times:
                        if 'start' in time_slot and 'end' in time_slot:
                            time_slots.append(f"{time_slot['start']} - {time_slot['end']}")
                    if time_slots:
                        zeitliche_verfuegbarkeit_text += f"{day_name}: {', '.join(time_slots)}; "
            
            patients_data.append({
                'diagnose': pr[1],
                'geschlecht': pr[2],
                'zeitliche_verfuegbarkeit_text': zeitliche_verfuegbarkeit_text.rstrip('; '),
                'beschwerden_seit': pr[4].strftime('%d.%m.%Y') if pr[4] else 'Unbekannt',
                'offen_fuer_gruppentherapie': pr[5] or False,
                'psychotherapieerfahrung': pr[6] or False,
                'aktuelle_psychische_beschwerden': pr[7] or ''
            })
        
        # Generate a batch ID
        batch_id = str(uuid.uuid4())
        
        # Determine email template based on number of patients
        template_name = (
            "emails/batch_request.html" if len(patients_data) > 1 
            else "emails/initial_contact.html"
        )
        
        # Create email subject
        subject = (
            f"Anfrage für {len(patients_data)} Therapieplätze" if len(patients_data) > 1
            else "Anfrage für einen Therapieplatz"
        )
        
        # Build recipient name
        recipient_name = ""
        if therapist_data['anrede']:
            recipient_name += therapist_data['anrede'] + " "
        if therapist_data['titel']:
            recipient_name += therapist_data['titel'] + " "
        recipient_name += therapist_data['nachname']
        
        # Render email template
        template_context = {
            'recipient_name': recipient_name,
            'patients': patients_data,
            'current_year': datetime.now().year
        }
        
        # For single patient emails, pass the patient directly
        if len(patients_data) == 1:
            template_context['patient'] = patients_data[0]
            
        body_html = render_template(template_name, **template_context)
        
        # Create a simple text version (this could be improved with HTML to text conversion)
        body_text = f"""Sehr geehrte(r) {recipient_name},

Wir haben {len(patients_data)} Patient(inn)en, für die wir einen Therapieplatz suchen.
Bitte prüfen Sie, ob Sie aktuell freie Kapazitäten haben.

Mit freundlichen Grüßen,
Boona Therapieplatz-Vermittlung
        """
        
        # Create email in database
        smtp_settings = get_smtp_settings()
        email = Email(
            therapist_id=therapist_id,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            recipient_email=therapist_data['email'],
            recipient_name=recipient_name,
            sender_email=smtp_settings['sender'],
            sender_name=smtp_settings['sender_name'],
            status=EmailStatus.DRAFT,
            batch_id=batch_id,
            placement_request_ids=placement_request_ids  # Temporary until fully migrated
        )
        
        db.add(email)
        db.flush()  # Get ID without committing
        
        # Create email batches
        for i, pr_id in enumerate(placement_request_ids):
            batch = EmailBatch(
                email_id=email.id,
                placement_request_id=pr_id,
                priority=i + 1  # Priority based on order
            )
            db.add(batch)
        
        db.commit()
        db.refresh(email)
        
        return email.id
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating batch email: {str(e)}")
        return None
    finally:
        db.close()


def send_email(email_id):
    """Send an email from the database.
    
    Args:
        email_id: ID of the email to send
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    db = SessionLocal()
    try:
        # Get the email from the database
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email with ID {email_id} not found")
            return False
        
        # Update status to SENDING
        email.status = EmailStatus.SENDING
        db.commit()
        
        # Create the email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email.subject
        msg['From'] = f"{email.sender_name} <{email.sender_email}>"
        msg['To'] = f"{email.recipient_name} <{email.recipient_email}>"
        
        # Attach the plain text version
        text_part = MIMEText(email.body_text, 'plain')
        msg.attach(text_part)
        
        # Attach the HTML version
        html_part = MIMEText(email.body_html, 'html')
        msg.attach(html_part)
        
        # Get SMTP settings
        smtp_settings = get_smtp_settings()
        
        # Send the email
        try:
            # Connect to the SMTP server
            if smtp_settings['use_tls']:
                server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
            
            # Login if credentials are provided
            if smtp_settings['username'] and smtp_settings['password']:
                server.login(smtp_settings['username'], smtp_settings['password'])
            
            # Send the email
            server.sendmail(
                email.sender_email,
                email.recipient_email,
                msg.as_string()
            )
            
            # Close the connection
            server.quit()
            
            # Update the email status
            email.status = EmailStatus.SENT
            email.sent_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Email {email_id} sent successfully")
            return True
            
        except Exception as e:
            # Update the email status
            email.status = EmailStatus.FAILED
            email.error_message = str(e)
            email.retry_count += 1
            db.commit()
            
            logger.error(f"Failed to send email {email_id}: {str(e)}")
            return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing email {email_id}: {str(e)}")
        return False
    finally:
        db.close()


def process_pending_requests():
    """Process pending placement requests and create batch emails.
    
    This function:
    1. Groups placement requests by therapist
    2. Checks therapist contact frequency (7-day rule)
    3. Creates batch emails for eligible therapists
    4. Queues the emails for sending
    
    Returns:
        int: Number of batch emails created
    """
    db = SessionLocal()
    try:
        # Get therapists with pending placement requests
        therapist_requests = db.execute(
            """
            SELECT pr.therapist_id, 
                   array_agg(pr.id) as request_ids,
                   array_agg(p.startdatum) as start_dates
            FROM matching_service.placement_requests pr
            JOIN patient_service.patients p ON pr.patient_id = p.id
            WHERE pr.status = 'offen'
            GROUP BY pr.therapist_id
            """,
        ).fetchall()
        
        batch_count = 0
        
        for record in therapist_requests:
            therapist_id = record[0]
            request_ids = record[1]
            start_dates = record[2]
            
            # Skip if no requests
            if not request_ids:
                continue
                
            # Check if therapist can be contacted (7-day rule)
            if not can_contact_therapist(therapist_id):
                logger.info(
                    f"Skipping therapist {therapist_id} due to contact frequency limit"
                )
                continue
            
            # Create a list of (request_id, start_date) tuples for sorting
            request_date_pairs = list(zip(request_ids, start_dates))
            
            # Sort by start date (oldest first)
            request_date_pairs.sort(key=lambda x: x[1] or datetime.max.date())
            
            # Extract sorted request IDs
            sorted_request_ids = [pair[0] for pair in request_date_pairs]
            
            # Create batch email
            email_id = create_batch_email(
                therapist_id=therapist_id,
                placement_request_ids=sorted_request_ids,
                priority_order=sorted_request_ids  # Use same order for priority
            )
            
            if email_id:
                # Queue the email for sending
                email = db.query(Email).get(email_id)
                email.status = EmailStatus.QUEUED
                email.queued_at = datetime.utcnow()
                db.commit()
                
                batch_count += 1
                logger.info(
                    f"Created and queued batch email {email_id} for "
                    f"therapist {therapist_id} with {len(sorted_request_ids)} requests"
                )
        
        return batch_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing pending requests: {str(e)}")
        return 0
    finally:
        db.close()


def send_queued_emails(limit=10):
    """Send emails from the queue.
    
    Args:
        limit: Maximum number of emails to send
        
    Returns:
        int: Number of emails sent
    """
    db = SessionLocal()
    try:
        logger.info("Starting send_queued_emails with systematic approach")
        
        # Method 1: Use a hybrid approach with direct value casting
        from sqlalchemy import cast, String, literal_column
        
        # Create a query that casts the status column to string and compares with the enum value
        query = db.query(Email).filter(
            cast(Email.status, String) == EmailStatus.QUEUED.value
        )
        
        # Log the actual SQL being generated
        sql_str = str(query.statement.compile(
            compile_kwargs={"literal_binds": True}
        ))
        logger.info(f"Generated SQL: {sql_str}")
        
        # Execute the query
        emails = query.order_by(Email.queued_at).limit(limit).all()
        
        logger.info(f"Found {len(emails)} emails with QUEUED status")
        
        sent_count = 0
        for email in emails:
            logger.info(f"Processing email {email.id} with status {email.status}")
            if send_email(email.id):
                sent_count += 1
        
        logger.info(f"Successfully sent {sent_count} emails")
        return sent_count
    except Exception as e:
        logger.error(f"Error sending queued emails: {str(e)}", exc_info=True)
        return 0
    finally:
        db.close()