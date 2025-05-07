"""Phone call scheduling utility functions."""
import logging
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Any

import requests
from sqlalchemy import and_

from shared.utils.database import SessionLocal
from models.phone_call import PhoneCall, PhoneCallStatus, PhoneCallBatch
from models.email import Email, EmailStatus

# Initialize logging
logger = logging.getLogger(__name__)

# Service URLs
THERAPIST_SERVICE_URL = "http://therapist-service:8002"
MATCHING_SERVICE_URL = "http://matching-service:8003"


def get_therapist_data(therapist_id: int) -> Optional[Dict[str, Any]]:
    """Get therapist data from the Therapist Service.

    Args:
        therapist_id: ID of the therapist

    Returns:
        Therapist data or None if not found
    """
    try:
        response = requests.get(
            f"{THERAPIST_SERVICE_URL}/api/therapists/{therapist_id}"
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error fetching therapist data: {str(e)}")
        return None


def parse_availability_slots(
    availability_data: Dict[str, List[Dict[str, str]]]
) -> Dict[int, List[Dict[str, str]]]:
    """Parse therapist availability data into day-indexed slots.
    
    Args:
        availability_data: Therapist availability JSON 
                          (e.g., {"monday": [{"start": "09:00", "end": "12:00"}]})
                          
    Returns:
        Dict mapping day of week (0=Monday, 6=Sunday) to list of time slots
    """
    day_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    result = {}
    
    for day_name, slots in availability_data.items():
        day_index = day_mapping.get(day_name.lower())
        if day_index is not None:
            result[day_index] = slots
            
    return result


def find_available_slot(
    therapist_id: int,
    start_date: date = None,
    duration_minutes: int = 5
) -> Optional[Dict[str, Any]]:
    """Find the next available time slot for a phone call.
    
    Args:
        therapist_id: ID of the therapist
        start_date: Date to start looking from (default: today)
        duration_minutes: Minimum duration required in minutes
        
    Returns:
        Dict with date, start and end time, or None if no slot found
    """
    # Default to today if no start date provided
    if start_date is None:
        start_date = date.today()
    
    # Get therapist data
    therapist_data = get_therapist_data(therapist_id)
    if not therapist_data:
        logger.error(f"Therapist {therapist_id} not found")
        return None
    
    # Get availability data
    availability = therapist_data.get('telefonische_erreichbarkeit', {}) or {}
    
    # Parse into day-indexed format
    day_slots = parse_availability_slots(availability)
    
    # Check for available slots starting from start_date
    for day_offset in range(14):  # Look up to 2 weeks ahead
        check_date = start_date + timedelta(days=day_offset)
        
        # Get day of week (0 = Monday, 6 = Sunday)
        day_of_week = check_date.weekday()
        
        # Check if there are slots for this day
        slots = day_slots.get(day_of_week, [])
        
        for slot in slots:
            start_time_str = slot.get('start')
            end_time_str = slot.get('end')
            
            if not start_time_str or not end_time_str:
                continue
                
            # Convert to datetime objects
            try:
                start_hour, start_minute = map(int, start_time_str.split(':'))
                end_hour, end_minute = map(int, end_time_str.split(':'))
                
                start_dt = datetime.combine(
                    check_date, 
                    time(hour=start_hour, minute=start_minute)
                )
                end_dt = datetime.combine(
                    check_date, 
                    time(hour=end_hour, minute=end_minute)
                )
                
                # Calculate duration in minutes
                duration = (end_dt - start_dt).total_seconds() / 60
                
                if duration >= duration_minutes:
                    # Check for existing calls in this time slot
                    if not is_slot_booked(therapist_id, check_date, start_time_str):
                        return {
                            'date': check_date,
                            'start_time': start_time_str,
                            'end_time': end_time_str,
                            'duration_minutes': duration
                        }
            except ValueError:
                logger.warning(
                    f"Invalid time format in therapist {therapist_id} availability: "
                    f"{start_time_str} - {end_time_str}"
                )
                continue
    
    return None


def is_slot_booked(
    therapist_id: int,
    call_date: date,
    start_time_str: str
) -> bool:
    """Check if a time slot is already booked for a therapist.
    
    Args:
        therapist_id: ID of the therapist
        call_date: Date of the proposed call
        start_time_str: Start time string (HH:MM)
        
    Returns:
        True if slot is already booked, False otherwise
    """
    db = SessionLocal()
    try:
        # Convert start_time string to time object
        start_hour, start_minute = map(int, start_time_str.split(':'))
        call_time = time(hour=start_hour, minute=start_minute)
        
        # Check for existing calls
        existing_call = db.query(PhoneCall).filter(
            PhoneCall.therapist_id == therapist_id,
            PhoneCall.scheduled_date == call_date,
            PhoneCall.scheduled_time == call_time,
            PhoneCall.status.in_([
                PhoneCallStatus.SCHEDULED.value,
                PhoneCallStatus.COMPLETED.value
            ])
        ).first()
        
        return existing_call is not None
    except Exception as e:
        logger.error(f"Error checking slot availability: {str(e)}")
        return True  # Assume booked if there's an error
    finally:
        db.close()


def schedule_call_for_email(email_id: int) -> Optional[int]:
    """Schedule a phone call for an unanswered email.
    
    Args:
        email_id: ID of the email that wasn't answered
        
    Returns:
        ID of the created phone call, or None if scheduling failed
    """
    db = SessionLocal()
    try:
        # Get the email
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email {email_id} not found")
            return None
        
        # Get placement requests for this email
        placement_request_ids = []
        
        # Check if we have batches relationship
        if hasattr(email, 'batches') and email.batches:
            placement_request_ids = [batch.placement_request_id for batch in email.batches]
        # Fall back to JSONB field
        elif email.placement_request_ids:
            placement_request_ids = email.placement_request_ids
            
        if not placement_request_ids:
            logger.error(f"No placement requests found for email {email_id}")
            return None
            
        # Find next available slot
        slot = find_available_slot(email.therapist_id)
        if not slot:
            logger.warning(
                f"No available slot found for therapist {email.therapist_id}"
            )
            return None
            
        # Create the phone call
        start_hour, start_minute = map(int, slot['start_time'].split(':'))
        call_time = time(hour=start_hour, minute=start_minute)
        
        phone_call = PhoneCall(
            therapist_id=email.therapist_id,
            scheduled_date=slot['date'],
            scheduled_time=call_time,
            duration_minutes=5,  # Default to 5 minutes
            status=PhoneCallStatus.SCHEDULED.value,
            notes=f"Follow-up call for unanswered email {email_id}",
        )
        
        db.add(phone_call)
        db.flush()  # Get ID without committing
        
        # Create batches for each placement request
        for pr_id in placement_request_ids:
            batch = PhoneCallBatch(
                phone_call_id=phone_call.id,
                placement_request_id=pr_id,
                priority=1  # Default priority
            )
            db.add(batch)
            
        db.commit()
        logger.info(
            f"Scheduled phone call {phone_call.id} for unanswered email {email_id}"
        )
        return phone_call.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling call for email {email_id}: {str(e)}")
        return None
    finally:
        db.close()


def schedule_follow_up_calls():
    """Schedule follow-up calls for emails that haven't been answered within 7 days.
    
    This function is meant to be run as a scheduled task.
    
    Returns:
        Number of calls scheduled
    """
    db = SessionLocal()
    try:
        # Find emails sent more than 7 days ago without a response
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        unanswered_emails = db.query(Email).filter(
            Email.sent_at <= seven_days_ago,
            Email.status == EmailStatus.SENT.value,
            Email.response_received.is_(False)
        ).all()
        
        logger.info(f"Found {len(unanswered_emails)} unanswered emails older than 7 days")
        
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