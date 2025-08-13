"""Email queue status tracking for monitoring."""
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import threading


class EmailQueueStatus:
    """Track email queue processing statistics and status."""
    
    # Class-level state
    _lock = threading.Lock()
    _status = {
        'running': True,
        'last_check': None,
        'emails_sent_today': 0,
        'emails_failed_today': 0,
        'last_error': None,
        'last_error_time': None,
        'total_sent': 0,
        'total_failed': 0,
        'current_date': date.today(),
        'recent_batches': []  # List of recent batch results
    }
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get current email queue status.
        
        Returns:
            Dictionary with current status
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['emails_sent_today'] = 0
                cls._status['emails_failed_today'] = 0
                cls._status['recent_batches'] = []
            
            return {
                'running': cls._status['running'],
                'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                'emails_sent_today': cls._status['emails_sent_today'],
                'emails_failed_today': cls._status['emails_failed_today'],
                'last_error': cls._status['last_error'],
                'last_error_time': cls._status['last_error_time'].isoformat() if cls._status['last_error_time'] else None,
                'total_sent': cls._status['total_sent'],
                'total_failed': cls._status['total_failed'],
                'recent_batches': cls._status['recent_batches'][-10:]  # Last 10 batches
            }
    
    @classmethod
    def get_health_status(cls) -> Dict:
        """Get health status for the email queue system.
        
        Returns:
            Dictionary with health status in same format as main health endpoint
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['emails_sent_today'] = 0
                cls._status['emails_failed_today'] = 0
                cls._status['recent_batches'] = []
            
            # Determine health status
            is_healthy = True
            issues = []
            
            # Check if processor is running
            if not cls._status['running']:
                is_healthy = False
                issues.append("Email queue processor not running")
            
            # Check for recent startup/critical errors
            if cls._status['last_error'] and cls._status['last_error_time']:
                error_age = datetime.utcnow() - cls._status['last_error_time']
                # If error is recent (within last 5 minutes)
                if error_age < timedelta(minutes=5):
                    is_healthy = False
                    issues.append("Recent error in queue processor")
            
            # Check failure rate for recent batches
            recent_batches = cls._status['recent_batches'][-20:]
            if len(recent_batches) >= 5:  # Only check if we have enough data
                total_sent = sum(batch.get('sent', 0) for batch in recent_batches)
                total_failed = sum(batch.get('failed', 0) for batch in recent_batches)
                
                if total_sent + total_failed > 0:
                    failure_rate = total_failed / (total_sent + total_failed)
                    if failure_rate > 0.5:  # More than 50% failure rate
                        is_healthy = False
                        issues.append(f"High failure rate: {failure_rate:.1%}")
            
            # Check if last check was too long ago (more than 5 minutes)
            if cls._status['last_check']:
                time_since_check = datetime.utcnow() - cls._status['last_check']
                if time_since_check > timedelta(minutes=5):
                    is_healthy = False
                    issues.append("Queue processor inactive for too long")
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'service': 'email-queue-processor',
                'details': {
                    'processor_running': cls._status['running'],
                    'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                    'emails_sent_today': cls._status['emails_sent_today'],
                    'emails_failed_today': cls._status['emails_failed_today'],
                    'last_error': cls._status['last_error'],
                    'last_error_time': cls._status['last_error_time'].isoformat() if cls._status['last_error_time'] else None,
                    'issues': issues
                }
            }
    
    @classmethod
    def update_last_check(cls):
        """Update the last check timestamp."""
        with cls._lock:
            cls._status['last_check'] = datetime.utcnow()
    
    @classmethod
    def record_emails_sent(cls, count: int):
        """Record successfully sent emails.
        
        Args:
            count: Number of emails sent
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['emails_sent_today'] = 0
                cls._status['emails_failed_today'] = 0
                cls._status['recent_batches'] = []
            
            cls._status['emails_sent_today'] += count
            cls._status['total_sent'] += count
            
            cls._status['recent_batches'].append({
                'sent': count,
                'failed': 0,
                'time': datetime.utcnow().isoformat()
            })
            
            # Keep only last 50 batches in memory
            if len(cls._status['recent_batches']) > 50:
                cls._status['recent_batches'] = cls._status['recent_batches'][-50:]
    
    @classmethod
    def record_email_failure(cls, count: int = 1):
        """Record failed email send attempts.
        
        Args:
            count: Number of emails that failed
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['emails_sent_today'] = 0
                cls._status['emails_failed_today'] = 0
                cls._status['recent_batches'] = []
            
            cls._status['emails_failed_today'] += count
            cls._status['total_failed'] += count
            
            cls._status['recent_batches'].append({
                'sent': 0,
                'failed': count,
                'time': datetime.utcnow().isoformat()
            })
            
            # Keep only last 50 batches in memory
            if len(cls._status['recent_batches']) > 50:
                cls._status['recent_batches'] = cls._status['recent_batches'][-50:]
    
    @classmethod
    def record_error(cls, error: str):
        """Record a general error (not email-specific).
        
        Args:
            error: Error message
        """
        with cls._lock:
            cls._status['last_error'] = error
            cls._status['last_error_time'] = datetime.utcnow()
    
    @classmethod
    def set_running(cls, running: bool):
        """Set the running status.
        
        Args:
            running: Whether the processor is running
        """
        with cls._lock:
            cls._status['running'] = running