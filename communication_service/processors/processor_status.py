"""Processor status tracking for monitoring Object Storage processing."""
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import threading


class ProcessorStatus:
    """Track processor statistics and status."""
    
    # Class-level state
    _lock = threading.Lock()
    _status = {
        'running': True,
        'last_check': None,
        # Verification emails
        'verifications_processed_today': 0,
        'verifications_failed_today': 0,
        # Contact forms
        'contacts_processed_today': 0,
        'contacts_failed_today': 0,
        # Waitlist verifications
        'waitlist_processed_today': 0,
        'waitlist_failed_today': 0,
        # General
        'last_error': None,
        'last_error_time': None,
        'total_processed': 0,
        'total_failed': 0,
        'current_date': date.today(),
        'recent_files': []  # List of recent processed files
    }
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get current processor status.
        
        Returns:
            Dictionary with current status
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            return {
                'running': cls._status['running'],
                'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                'verifications_processed_today': cls._status['verifications_processed_today'],
                'verifications_failed_today': cls._status['verifications_failed_today'],
                'contacts_processed_today': cls._status['contacts_processed_today'],
                'contacts_failed_today': cls._status['contacts_failed_today'],
                'waitlist_processed_today': cls._status['waitlist_processed_today'],
                'waitlist_failed_today': cls._status['waitlist_failed_today'],
                'last_error': cls._status['last_error'],
                'last_error_time': cls._status['last_error_time'].isoformat() if cls._status['last_error_time'] else None,
                'total_processed': cls._status['total_processed'],
                'total_failed': cls._status['total_failed'],
                'recent_files': cls._status['recent_files'][-10:]  # Last 10 files
            }
    
    @classmethod
    def get_health_status(cls) -> Dict:
        """Get health status for the processor system.
        
        Returns:
            Dictionary with health status in same format as main health endpoint
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            # Determine health status
            is_healthy = True
            issues = []

            # Check if processor is running
            if not cls._status['running']:
                is_healthy = False
                issues.append("Storage processor not running")

            # Check for recent startup/critical errors
            if cls._status['last_error'] and cls._status['last_error_time']:
                error_age = datetime.utcnow() - cls._status['last_error_time']
                # If error is recent (within last hour)
                if error_age < timedelta(hours=1):
                    is_healthy = False
                    issues.append("Recent processor error")

            # Check failure rate for recent files
            recent_files = cls._status['recent_files'][-20:]
            if len(recent_files) >= 5:  # Only check if we have enough data
                failed_recent = sum(1 for f in recent_files if f.get('status') == 'failed')
                failure_rate = failed_recent / len(recent_files)
                if failure_rate > 0.5:  # More than 50% failure rate
                    is_healthy = False
                    issues.append(f"High failure rate: {failure_rate:.1%}")

            # Check if last check was too long ago (more than 5 minutes)
            if cls._status['last_check']:
                time_since_check = datetime.utcnow() - cls._status['last_check']
                if time_since_check > timedelta(minutes=5):
                    is_healthy = False
                    issues.append("Processor inactive for too long")

            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'service': 'storage-processor',
                'details': {
                    'processor_running': cls._status['running'],
                    'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                    'verifications_processed_today': cls._status['verifications_processed_today'],
                    'contacts_processed_today': cls._status['contacts_processed_today'],
                    'waitlist_processed_today': cls._status['waitlist_processed_today'],
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
    def record_verification_success(cls, file_name: str):
        """Record a successful verification email.
        
        Args:
            file_name: Name of the processed file
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            cls._status['verifications_processed_today'] += 1
            cls._status['total_processed'] += 1
            cls._status['recent_files'].append({
                'file': file_name,
                'type': 'verification',
                'status': 'success',
                'time': datetime.utcnow().isoformat()
            })

            # Keep only last 50 files in memory
            if len(cls._status['recent_files']) > 50:
                cls._status['recent_files'] = cls._status['recent_files'][-50:]
    
    @classmethod
    def record_verification_failure(cls, file_name: str, error: str):
        """Record a failed verification email.
        
        Args:
            file_name: Name of the file that failed
            error: Error message
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            cls._status['verifications_failed_today'] += 1
            cls._status['total_failed'] += 1
            cls._status['last_error'] = f"Verification {file_name}: {error}"
            cls._status['last_error_time'] = datetime.utcnow()
            cls._status['recent_files'].append({
                'file': file_name,
                'type': 'verification',
                'status': 'failed',
                'error': error,
                'time': datetime.utcnow().isoformat()
            })

            # Keep only last 50 files in memory
            if len(cls._status['recent_files']) > 50:
                cls._status['recent_files'] = cls._status['recent_files'][-50:]
    
    @classmethod
    def record_contact_success(cls, file_name: str):
        """Record a successful contact form.
        
        Args:
            file_name: Name of the processed file
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            cls._status['contacts_processed_today'] += 1
            cls._status['total_processed'] += 1
            cls._status['recent_files'].append({
                'file': file_name,
                'type': 'contact',
                'status': 'success',
                'time': datetime.utcnow().isoformat()
            })

            # Keep only last 50 files in memory
            if len(cls._status['recent_files']) > 50:
                cls._status['recent_files'] = cls._status['recent_files'][-50:]
    
    @classmethod
    def record_contact_failure(cls, file_name: str, error: str):
        """Record a failed contact form.
        
        Args:
            file_name: Name of the file that failed
            error: Error message
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            cls._status['contacts_failed_today'] += 1
            cls._status['total_failed'] += 1
            cls._status['last_error'] = f"Contact {file_name}: {error}"
            cls._status['last_error_time'] = datetime.utcnow()
            cls._status['recent_files'].append({
                'file': file_name,
                'type': 'contact',
                'status': 'failed',
                'error': error,
                'time': datetime.utcnow().isoformat()
            })

            # Keep only last 50 files in memory
            if len(cls._status['recent_files']) > 50:
                cls._status['recent_files'] = cls._status['recent_files'][-50:]
    
    @classmethod
    def record_error(cls, error: str):
        """Record a general error (not file-specific).
        
        Args:
            error: Error message
        """
        with cls._lock:
            cls._status['last_error'] = error
            cls._status['last_error_time'] = datetime.utcnow()
    
    @classmethod
    def record_waitlist_success(cls, file_name: str):
        """Record a successful waitlist verification email.

        Args:
            file_name: Name of the processed file
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            cls._status['waitlist_processed_today'] += 1
            cls._status['total_processed'] += 1
            cls._status['recent_files'].append({
                'file': file_name,
                'type': 'waitlist',
                'status': 'success',
                'time': datetime.utcnow().isoformat()
            })

            # Keep only last 50 files in memory
            if len(cls._status['recent_files']) > 50:
                cls._status['recent_files'] = cls._status['recent_files'][-50:]

    @classmethod
    def record_waitlist_failure(cls, file_name: str, error: str):
        """Record a failed waitlist verification email.

        Args:
            file_name: Name of the file that failed
            error: Error message
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['verifications_processed_today'] = 0
                cls._status['verifications_failed_today'] = 0
                cls._status['contacts_processed_today'] = 0
                cls._status['contacts_failed_today'] = 0
                cls._status['waitlist_processed_today'] = 0
                cls._status['waitlist_failed_today'] = 0
                cls._status['recent_files'] = []

            cls._status['waitlist_failed_today'] += 1
            cls._status['total_failed'] += 1
            cls._status['last_error'] = f"Waitlist {file_name}: {error}"
            cls._status['last_error_time'] = datetime.utcnow()
            cls._status['recent_files'].append({
                'file': file_name,
                'type': 'waitlist',
                'status': 'failed',
                'error': error,
                'time': datetime.utcnow().isoformat()
            })

            # Keep only last 50 files in memory
            if len(cls._status['recent_files']) > 50:
                cls._status['recent_files'] = cls._status['recent_files'][-50:]

    @classmethod
    def set_running(cls, running: bool):
        """Set the running status.

        Args:
            running: Whether the processor is running
        """
        with cls._lock:
            cls._status['running'] = running