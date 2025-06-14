"""Phone call scheduling utility functions - simplified to basic database operations only."""
import logging
from datetime import date, datetime, time, timedelta
from typing import Dict, Optional, Any

from shared.utils.database import SessionLocal
from models.phone_call import PhoneCall, PhoneCallStatus
from shared.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


def find_available_slot(
    therapist_id: int,
    start_date: Optional[date] = None,
    duration_minutes: int = 5
) -> Optional[Dict[str, Any]]:
    """Find the next available time slot for a therapist.
    
    This is a simplified version that just returns a default slot
    since complex scheduling algorithms have been moved out.
    
    Args:
        therapist_id: ID of the therapist
        start_date: Date to start searching from (default: today)
        duration_minutes: Required duration in minutes
        
    Returns:
        Dict with slot information or None if no slot found
    """
    if start_date is None:
        start_date = date.today()
    
    # Simple implementation: return tomorrow at 10:00 AM
    # More complex scheduling logic should be implemented in the requesting service
    tomorrow = start_date + timedelta(days=1)
    
    # Check if this basic slot is available
    if not is_slot_booked(therapist_id, tomorrow, "10:00", duration_minutes):
        return {
            "date": tomorrow.isoformat(),
            "start_time": "10:00",
            "duration_minutes": duration_minutes,
            "day_name": tomorrow.strftime("%A").lower()
        }
    
    # If 10:00 is booked, try 14:00
    if not is_slot_booked(therapist_id, tomorrow, "14:00", duration_minutes):
        return {
            "date": tomorrow.isoformat(),
            "start_time": "14:00",
            "duration_minutes": duration_minutes,
            "day_name": tomorrow.strftime("%A").lower()
        }
    
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
    
    This is now a simplified implementation. Complex scheduling logic
    should be handled by the requesting service.
    
    Args:
        email_id: ID of the email that needs follow-up
        
    Returns:
        ID of the created phone call or None if scheduling failed
    """
    db = SessionLocal()
    try:
        from models.email import Email
        
        # Get the email
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email {email_id} not found")
            return None
        
        # Only handle therapist emails for now
        if not email.therapist_id:
            logger.warning(f"Email {email_id} is not for a therapist")
            return None
        
        # Find a simple available slot
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
        db.refresh(phone_call)
        
        logger.info(f"Scheduled follow-up call {phone_call.id} for email {email_id}")
        return phone_call.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling call for email {email_id}: {str(e)}")
        return None
    finally:
        db.close()
