"""Communication service utility functions."""
from .email_queue_processor import start_email_queue_processor
from .email_status import EmailQueueStatus

__all__ = ['start_email_queue_processor', 'EmailQueueStatus']