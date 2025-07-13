"""Import status tracking for monitoring."""
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import threading


class ImportStatus:
    """Track import statistics and status."""
    
    # Class-level state
    _lock = threading.Lock()
    _status = {
        'running': True,
        'last_check': None,
        'files_processed_today': 0,
        'files_failed_today': 0,
        'last_error': None,
        'last_error_time': None,
        'total_processed': 0,
        'total_failed': 0,
        'current_date': date.today(),
        'recent_imports': []  # List of recent file names
    }
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get current import status.
        
        Returns:
            Dictionary with current status
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['files_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            return {
                'running': cls._status['running'],
                'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                'files_processed_today': cls._status['files_processed_today'],
                'files_failed_today': cls._status['files_failed_today'],
                'last_error': cls._status['last_error'],
                'last_error_time': cls._status['last_error_time'].isoformat() if cls._status['last_error_time'] else None,
                'total_processed': cls._status['total_processed'],
                'total_failed': cls._status['total_failed'],
                'recent_imports': cls._status['recent_imports'][-10:]  # Last 10 imports
            }
    
    @classmethod
    def get_health_status(cls) -> Dict:
        """Get health status for the import system.
        
        Returns:
            Dictionary with health status in same format as main health endpoint
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['files_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            # Determine health status
            is_healthy = True
            issues = []
            
            # Check if monitor is running
            if not cls._status['running']:
                is_healthy = False
                issues.append("Import monitor not running")
            
            # Check for recent startup/critical errors
            if cls._status['last_error'] and cls._status['last_error_time']:
                error_age = datetime.utcnow() - cls._status['last_error_time']
                # If error is recent (within last hour) and we haven't processed files since
                if error_age < timedelta(hours=1) and cls._status['last_check'] is None:
                    is_healthy = False
                    issues.append("Recent startup error")
            
            # Check failure rate for recent imports (last 20 imports)
            recent_imports = cls._status['recent_imports'][-20:]
            if len(recent_imports) >= 5:  # Only check if we have enough data
                failed_recent = sum(1 for imp in recent_imports if imp.get('status') == 'failed')
                failure_rate = failed_recent / len(recent_imports)
                if failure_rate > 0.5:  # More than 50% failure rate
                    is_healthy = False
                    issues.append(f"High failure rate: {failure_rate:.1%}")
            
            # Check if last check was too long ago (more than 1 hour)
            if cls._status['last_check']:
                time_since_check = datetime.utcnow() - cls._status['last_check']
                if time_since_check > timedelta(hours=1):
                    is_healthy = False
                    issues.append("Monitor inactive for too long")
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'service': 'patient-import-monitor',
                'details': {
                    'monitor_running': cls._status['running'],
                    'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                    'files_processed_today': cls._status['files_processed_today'],
                    'files_failed_today': cls._status['files_failed_today'],
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
    def record_success(cls, file_name: str):
        """Record a successful import.
        
        Args:
            file_name: Name of the imported file
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['files_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            cls._status['files_processed_today'] += 1
            cls._status['total_processed'] += 1
            cls._status['recent_imports'].append({
                'file': file_name,
                'status': 'success',
                'time': datetime.utcnow().isoformat()
            })
            
            # Keep only last 50 imports in memory
            if len(cls._status['recent_imports']) > 50:
                cls._status['recent_imports'] = cls._status['recent_imports'][-50:]
    
    @classmethod
    def record_failure(cls, file_name: str, error: str):
        """Record a failed import.
        
        Args:
            file_name: Name of the file that failed
            error: Error message
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['files_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            cls._status['files_failed_today'] += 1
            cls._status['total_failed'] += 1
            cls._status['last_error'] = f"{file_name}: {error}"
            cls._status['last_error_time'] = datetime.utcnow()
            cls._status['recent_imports'].append({
                'file': file_name,
                'status': 'failed',
                'error': error,
                'time': datetime.utcnow().isoformat()
            })
            
            # Keep only last 50 imports in memory
            if len(cls._status['recent_imports']) > 50:
                cls._status['recent_imports'] = cls._status['recent_imports'][-50:]
    
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
    def set_running(cls, running: bool):
        """Set the running status.
        
        Args:
            running: Whether the import is running
        """
        with cls._lock:
            cls._status['running'] = running