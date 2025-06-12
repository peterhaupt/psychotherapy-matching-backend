"""Phone call scheduling utility functions."""
import logging
from datetime import date, datetime, time, timedelta
from typing import Dict, Optional, Any

import requests

from shared.utils.database import SessionLocal
from models.phone_call import PhoneCall, PhoneCallStatus
from models.email import Email, EmailStatus
from shared.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Service URLs from configuration
THERAPIST_SERVICE_URL = config.get_service_url("therapist", internal=True)
MATCHING_SERVICE_URL = config.get_service_url("matching", internal=True)


def find_available_slot(
    therapist_id: int,
    start_date: Optional[date] = None,
    duration_minutes: int = 5
) -> Optional[Dict[str, Any]]:
    """Find the next available time slot for a therapist.
    
    Args:
        therapist_id: ID of the therapist
        start_date: Date to start searching from (default: today)
        duration_minutes: Required duration in minutes
        
    Returns:
        Dict with slot information or None if no slot found
    """
    if start_date is None:
        start_date = date.today()
    
    # Get therapist data
    try:
        response = requests.get(f"{THERAPIST_SERVICE_URL}/api/therapists/{therapist_id}")
        if response.status_code != 200:
            logger.error(f"Failed to get therapist {therapist_id}: {response.status_code}")
            return None
            
        therapist = response.json()
    except Exception as e:
        logger.error(f"Error fetching therapist {therapist_id}: {str(e)}")
        return None
    
    # Get phone availability
    phone_availability = therapist.get("telefonische_erreichbarkeit", {})
    if not phone_availability:
        logger.warning(f"Therapist {therapist_id} has no phone availability")
        return None
    
    # Check next 14 days
    for day_offset in range(14):
        check_date = start_date + timedelta(days=day_offset)
        day_name = check_date.strftime("%A").lower()
        
        # Get slots for this day
        day_slots = phone_availability.get(day_name, [])
        
        for slot in day_slots:
            start_time = slot.get("start")
            end_time = slot.get("end")
            
            if not start_time or not end_time:
                continue
            
            # Parse times
            try:
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = datetime.strptime(end_time, "%H:%M")
            except ValueError:
                logger.warning(f"Invalid time format for therapist {therapist_id}: {start_time} - {end_time}")
                continue
            
            # Calculate slot duration
            slot_duration = (end_dt - start_dt).total_seconds() / 60
            
            # Check if slot is long enough
            if slot_duration < duration_minutes:
                continue
            
            # Check for existing calls in this slot
            current_time = start_dt
            while current_time + timedelta(minutes=duration_minutes) <= end_dt:
                time_str = current_time.strftime("%H:%M")
                
                if not is_slot_booked(therapist_id, check_date, time_str, duration_minutes):
                    return {
                        "date": check_date.isoformat(),
                        "start_time": time_str,
                        "duration_minutes": duration_minutes,
                        "day_name": day_name
                    }
                
                # Move to next 5-minute slot
                current_time += timedelta(minutes=5)
    
    return None


def is_slot_booked(
    therapist_id: int,
    date_obj: date,
    start_time: str,
    duration_minutes: int
) -> bool:
    """Check if a time slot is already booked.
    
    Args:
        therapist_id: ID of the therapist
        date_obj: Date to check
        start_time: Start time in HH:MM format
        duration_minutes: Duration to check
        
    Returns:
        True if slot is booked, False otherwise
    """
    db = SessionLocal()
    try:
        # Parse time
        hour, minute = map(int, start_time.split(":"))
        time_obj = time(hour=hour, minute=minute)
        
        # Check for existing calls
        existing_calls = db.query(PhoneCall).filter(
            PhoneCall.therapist_id == therapist_id,
            PhoneCall.geplantes_datum == date_obj,
            PhoneCall.geplante_zeit == time_obj,
            PhoneCall.status != PhoneCallStatus.abgebrochen.value
        ).count()
        
        return existing_calls > 0
        
    except Exception as e:
        logger.error(f"Error checking slot availability: {str(e)}")
        return True  # Assume booked on error
    finally:
        db.close()


def schedule_call_for_email(email_id: int) -> Optional[int]:
    """Schedule a follow-up phone call for an unanswered email.
    
    Args:
        email_id: ID of the email that needs follow-up
        
    Returns:
        ID of the created phone call or None if scheduling failed
    """
    db = SessionLocal()
    try:
        # Get the email
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email {email_id} not found")
            return None
        
        # Find available slot
        slot = find_available_slot(email.therapist_id)
        if not slot:
            logger.warning(f"No available slot found for therapist {email.therapist_id}")
            return None
        
        # Create phone call
        scheduled_date = datetime.fromisoformat(slot["date"]).date()
        hour, minute = map(int, slot["start_time"].split(":"))
        scheduled_time = time(hour=hour, minute=minute)
        
        phone_call = PhoneCall(
            therapist_id=email.therapist_id,
            geplantes_datum=scheduled_date,
            geplante_zeit=scheduled_time,
            dauer_minuten=slot["duration_minutes"],
            status=PhoneCallStatus.geplant.value,
            notizen=f"Follow-up for email {email_id}"
        )
        
        db.add(phone_call)
        db.commit()
        
        logger.info(f"Scheduled follow-up call {phone_call.id} for email {email_id}")
        return phone_call.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling call for email {email_id}: {str(e)}")
        return None
    finally:
        db.close()


def schedule_follow_up_calls(days_threshold: int = 7) -> int:
    """Schedule follow-up calls for all unanswered emails.
    
    Args:
        days_threshold: Days after sending to schedule follow-up
        
    Returns:
        Number of calls scheduled
    """
    db = SessionLocal()
    try:
        # Find emails that need follow-up
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        unanswered_emails = db.query(Email).filter(
            Email.gesendet_am <= threshold_date,
            Email.status == EmailStatus.Gesendet.value,
            Email.antwort_erhalten.is_(False)
        ).all()
        
        scheduled_count = 0
        
        for email in unanswered_emails:
            call_id = schedule_call_for_email(email.id)
            if call_id:
                scheduled_count += 1
        
        logger.info(f"Scheduled {scheduled_count} follow-up calls")
        return scheduled_count
        
    except Exception as e:
        logger.error(f"Error scheduling follow-up calls: {str(e)}")
        return 0
    finally:
        db.close()