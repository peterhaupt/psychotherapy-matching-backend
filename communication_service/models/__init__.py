"""Communication service models package."""
from .email import Email, EmailStatus
from .phone_call import PhoneCall, PhoneCallStatus

__all__ = [
    'Email', 
    'EmailStatus',
    'PhoneCall',
    'PhoneCallStatus'
]